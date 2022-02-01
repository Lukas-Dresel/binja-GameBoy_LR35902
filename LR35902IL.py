#!/usr/bin/env python
#
# separate module for lifting, two main exports:
# gen_flag_il()
# gen_instr_il()

# Binja includes
from tempfile import tempdir
from binaryninja.log import log_info
from binaryninja.architecture import Architecture
from binaryninja.enums import LowLevelILOperation, LowLevelILFlagCondition
from binaryninja.function import RegisterInfo, InstructionInfo, InstructionTextToken
from binaryninja.lowlevelil import LowLevelILLabel, ILRegister, ILFlag, LLIL_TEMP, LLIL_GET_TEMP_REG_INDEX

# decode/disassemble
from lr35902dis.lr35902 import *

#------------------------------------------------------------------------------
# LOOKUP TABLES
#------------------------------------------------------------------------------

REG_TO_SIZE = {
    REG.A:1, REG.F:1,
    REG.B:1, REG.C:1,
    REG.D:1, REG.E:1,
    REG.H:1, REG.L:1,
    REG.AF:2,
    REG.BC:2,
    REG.DE:2,
    REG.HL:2,

    REG.SP:2,
    REG.PC:2
}

CC_UN_NOT = {
    CC.NOT_Z:CC.Z, CC.NOT_C:CC.C,
}

#------------------------------------------------------------------------------
# HELPERS
#------------------------------------------------------------------------------

def jcc_to_flag_cond(cond, il):
    if cond == CC.ALWAYS:
        return il.const(1,1)

    # {'z', 'nz'} == {'zero', 'not zero'}
    if cond == CC.Z:
        return il.flag_condition(LowLevelILFlagCondition.LLFC_E)
    if cond == CC.NOT_Z:
        return il.flag_condition(LowLevelILFlagCondition.LLFC_NE)

    # {'c', 'nc'} == {'carry', 'not carry'}
    if cond == CC.C:
        return il.flag('c')
    if cond == CC.NOT_C:
        return il.not_expr(0, il.flag('c'))

    raise Exception('unknown cond: ' + str(cond))

def goto_or_jump(target_type, target_val, il):
    if target_type == OPER_TYPE.ADDR:
        tmp = il.get_label_for_address(Architecture['LR35902'], target_val)
        if tmp:
            return il.goto(tmp)
        else:
            return il.jump(il.const_pointer(2, target_val))
    else:
        tmp = operand_to_il(target_type, target_val, il, 2)
        return il.jump(tmp)

def append_conditional_instr(cond, instr, il):
    if cond == CC.ALWAYS:
        il.append(instr)
    else:
        t = LowLevelILLabel()
        f = LowLevelILLabel()
        #if cond in CC_UN_NOT:
        #    ant = jcc_to_flag_cond(CC_UN_NOT[cond], il)
        #    il.append(il.if_expr(ant, f, t))
        #else:
        ant = jcc_to_flag_cond(cond, il)
        il.append(il.if_expr(ant, t, f))
        il.mark_label(t)
        il.append(instr)
        il.mark_label(f)

def append_conditional_jump(cond, target_type, target_val, addr_fallthru, il):
    # case: condition always
    if cond == CC.ALWAYS:
        il.append(goto_or_jump(target_type, target_val, il))
        return

    # case: condition and label available
    if target_type == OPER_TYPE.ADDR:
        t = il.get_label_for_address(Architecture['LR35902'], target_val)
        f = il.get_label_for_address(Architecture['LR35902'], addr_fallthru)
        if t and f:
            #if cond in CC_UN_NOT:
            #    ant = jcc_to_flag_cond(CC_UN_NOT[cond], il)
            #    il.append(il.if_expr(ant, f, t))
            #else:
            ant = jcc_to_flag_cond(cond, il)
            il.append(il.if_expr(ant, t, f))
            return

    # case: conditional and address available
    tmp = goto_or_jump(target_type, target_val, il)
    append_conditional_instr(cond, tmp, il)

def operand_to_il(oper_type, oper_val, il, size_hint=0, peel_load=False):
    if oper_type == OPER_TYPE.REG:
        return il.reg(REG_TO_SIZE[oper_val], reg2str(oper_val))

    elif oper_type in [OPER_TYPE.REG_DEREF, OPER_TYPE.REG_DEREF_INC, OPER_TYPE.REG_DEREF_DEC] :
        tmp = operand_to_il(OPER_TYPE.REG, oper_val, il, size_hint)
        if peel_load:
            return tmp
        else:
            return il.load(size_hint, tmp)

    elif oper_type == OPER_TYPE.REG_DEREF_FF00:
        assert oper_val == REG.C
        tmp = il.add(2,
            il.const(2, 0xff00),
            il.zero_extend(2, il.reg(1, 'C'))
        )
        if peel_load:
            return tmp
        else:
            return il.load(1, tmp)

    elif oper_type == OPER_TYPE.ADDR:
        return il.const_pointer(2, oper_val)

    elif oper_type == OPER_TYPE.ADDR_DEREF:
        tmp = il.const_pointer(2, oper_val)
        if peel_load:
            return tmp
        else:
            return il.load(size_hint, tmp)

    elif oper_type == OPER_TYPE.ADDR_DEREF_FF00:
        tmp = il.const(2, 0xff00 + (oper_val & 0xff))
        return tmp if peel_load else il.load(1, tmp)

    elif oper_type == OPER_TYPE.SP_OFFSET:
        if oper_val & 0x80:
            oper_val, = struct.unpack("<b", bytes([oper_val]))
        return il.add(2, il.reg(2, 'SP'), il.const(2, oper_val))

    elif oper_type == OPER_TYPE.IMM:
        return il.const(size_hint, oper_val)

    elif oper_type == OPER_TYPE.COND:
        return il.unimplemented()

    else:
        raise Exception("unknown operand type: " + str(oper_type))

def expressionify(size, foo, il, temps_are_conds=False):
    """ turns the "reg or constant"  operands to get_flag_write_low_level_il()
        into lifted expressions """
    if isinstance(foo, int):
        return foo

    if isinstance(foo, ILRegister):
        # LowLevelILExpr is different than ILRegister
        if temps_are_conds and LLIL_TEMP(foo.index):
            # can't use il.reg() 'cause it will do lookup in architecture flags
            return il.expr(LowLevelILOperation.LLIL_FLAG, foo)
            #return il.reg(size, 'cond:%d' % LLIL_GET_TEMP_REG_INDEX(foo))

        # promote it to an LLIL_REG (read register)
        return il.reg(size, foo)

    elif isinstance(foo, ILFlag):
        return il.flag(foo)

    elif isinstance(foo, int):
        return il.const(size, foo)

    else:
        raise Exception('expressionify() doesn\'t know how to handle il: %s\n%s\n' % (foo, type(foo)))

#------------------------------------------------------------------------------
# FLAG LIFTING
#------------------------------------------------------------------------------
#        il.append(il.set_flag('z', il.xor_expr(1, il.test_bit(1, operand, mask), il.const(1, 1))))
#        il.append(il.set_flag('n', il.const(0, 0)))
#        il.append(il.set_flag('h', il.const(0, 0)))

def gen_flag_il(op, size, write_type, flag, operands, il):
    if op in {LowLevelILOperation.LLIL_ASR, LowLevelILOperation.LLIL_LSR}:
        if flag == 'c':
            return il.test_bit(1, expressionify(size, operands[0], il), il.const(1, 1))
        else:
            return None
    if flag == 'c':
        if op == LowLevelILOperation.LLIL_SBB:
            lhs = expressionify(size, operands[1], il)
            rhs = expressionify(1, operands[2], il, True)
            cmp = expressionify(size, operands[0], il)
            return il.compare_signed_greater_than(size,
                il.add(size,
                    lhs,
                    rhs
                ),
                cmp
            )

        if op == LowLevelILOperation.LLIL_OR:
            return il.const(1, 0)
        if op == LowLevelILOperation.LLIL_ASR:
            assert False
            return il.test_bit(1, expressionify(size, operands[0], il), il.const(1, 1))
        if op == LowLevelILOperation.LLIL_POP:
            return il.set_flag('c', il.test_bit(1, il.reg(1, 'F'), il.const(1, 1)))
        if op == LowLevelILOperation.LLIL_RLC:
            return il.test_bit(1, il.reg(size, operands[0]), il.const(1, 0x80))
        if op == LowLevelILOperation.LLIL_ROL:
            return il.test_bit(1, il.reg(size, operands[0]), il.const(1, 0x80))
        if op == LowLevelILOperation.LLIL_RRC:
            return il.test_bit(1, il.reg(size, operands[0]), il.const(1, 1))
        if op == LowLevelILOperation.LLIL_ROR:
            return il.test_bit(1, il.reg(size, operands[0]), il.const(1, 1))
        if op == LowLevelILOperation.LLIL_XOR:
            return il.const(1, 0)

    if flag == 'h':
        if op == LowLevelILOperation.LLIL_POP:
            return il.set_flag('h', il.test_bit(1, il.reg(1, 'F'), il.const(1, 1<<4)))
        if op == LowLevelILOperation.LLIL_XOR:
            return il.const(1, 0)

    if flag == 'z':
        bin_mapping = {
            LowLevelILOperation.LLIL_XOR: il.xor_expr,
            LowLevelILOperation.LLIL_OR: il.or_expr,
            LowLevelILOperation.LLIL_AND: il.and_expr,
            # LowLevelILOperation.LLIL_ADD: il.add,
            LowLevelILOperation.LLIL_SUB: il.sub,
        }
        if op in bin_mapping:
            return il.compare_equal(size,
                bin_mapping[op](size,
                    expressionify(size, operands[0], il),
                    expressionify(size, operands[1], il),
                ),
                il.const(1, 0)
            )

    return None

def append_store_result(loc_type, loc_val, size, expr, il):
    deref_src_addr_map = {
        OPER_TYPE.REG_DEREF: lambda: il.reg(2, loc_val.name),
        OPER_TYPE.REG_DEREF_DEC: lambda: il.reg(2, loc_val.name),
        OPER_TYPE.REG_DEREF_INC: lambda: il.reg(2, loc_val.name),
        OPER_TYPE.REG_DEREF_FF00: lambda: il.add(2, il.reg(2, loc_val.name), il.const_pointer(2, 0xff00)),
        OPER_TYPE.ADDR_DEREF: lambda: il.const_pointer(2, loc_val),
        OPER_TYPE.ADDR_DEREF_FF00: lambda: il.const_pointer(2, 0xff00 + loc_val),
    }
    update_map = {
        OPER_TYPE.REG_DEREF_INC: lambda: il.set_reg(2, 'HL', il.add(2, il.reg(2, 'HL'), il.const(2, 1))),
        OPER_TYPE.REG_DEREF_DEC: lambda: il.set_reg(2, 'HL', il.sub(2, il.reg(2, 'HL'), il.const(2, 1))),
    }
    if loc_type in deref_src_addr_map:
        target_addr = deref_src_addr_map[loc_type]()
        il.append(il.store(size, target_addr, expr))
        if loc_type in update_map:
            il.append(update_map[loc_type]())

    elif loc_type == OPER_TYPE.REG:
        il.append(il.set_reg(size, loc_val.name, expr))

    else:
        assert False, f"WHHAAAAAt are you trying to store into?? {loc_type=}, {loc_val=}, {size=}, {expr=}, {il=}"

#------------------------------------------------------------------------------
# INSTRUCTION LIFTING
#------------------------------------------------------------------------------

def gen_instr_il(addr, decoded, il):
    (oper_type, oper_val) = decoded.operands[0] if decoded.operands else (None, None)
    (operb_type, operb_val) = decoded.operands[1] if decoded.operands[1:] else (None, None)

    if decoded.op in [OP.ADD, OP.ADC]:
        assert len(decoded.operands) == 2
        if oper_type == OPER_TYPE.REG:
            size = REG_TO_SIZE[oper_val]
            rhs = operand_to_il(operb_type, operb_val, il, size)
            lhs = operand_to_il(oper_type, oper_val, il)
            if decoded.op == OP.ADD:
                tmp = il.add(size, lhs, rhs, flags='*')
            else:
                tmp = il.add_carry(size, lhs, rhs, il.flag("c"), flags='*')
            tmp = il.set_reg(size, reg2str(oper_val), tmp)
            il.append(tmp)
        else:
            il.append(il.unimplemented())

    elif decoded.op == OP.AND:
        tmp = il.reg(1, 'A')
        tmp = il.and_expr(1, operand_to_il(oper_type, oper_val, il, 1), tmp, flags='z')
        tmp = il.set_reg(1, 'A', tmp)
        il.append(tmp)

    elif decoded.op == OP.BIT:
        assert oper_type == OPER_TYPE.IMM
        assert oper_val >= 0 and oper_val <= 7
        mask = il.const(1, 1<<oper_val)
        operand = operand_to_il(operb_type, operb_val, il, 1)
        il.append(il.and_expr(1, operand, mask, flags='*'))

    elif decoded.op == OP.CALL:
        condition, target = (oper_val, operb_val) if oper_type == OPER_TYPE.COND else (CC.ALWAYS, oper_val)
        append_conditional_instr(condition, il.call(il.const_pointer(2, target)), il)

    elif decoded.op == OP.RST:
        assert oper_type == OPER_TYPE.IMM
        il.append(il.const_pointer(2, oper_val))

    elif decoded.op == OP.SCF:
        il.append(il.set_flag('c', il.const(0, 1)))

    elif decoded.op == OP.CCF:
        il.append(il.set_flag('c', il.not_expr(0, il.flag('c'))))

    elif decoded.op == OP.CP:
        # sub, but do not write to register
        lhs = il.reg(1, 'A')
        rhs = operand_to_il(oper_type, oper_val, il, 1)
        sub = il.sub(1, lhs, rhs, flags='*')
        il.append(sub)

    elif decoded.op == OP.INC:
        # inc reg can be 1-byte or 2-byte
        if oper_type == OPER_TYPE.REG:
            size = REG_TO_SIZE[oper_val]
            tmp = il.add(size, operand_to_il(oper_type, oper_val, il), il.const(1, 1))
            tmp = il.set_reg(size, reg2str(oper_val), tmp)
        else:
            tmp = il.add(1, operand_to_il(oper_type, oper_val, il), il.const(1, 1))
            tmp = il.store(1, operand_to_il(oper_type, oper_val, il, 1, peel_load=True), tmp)

        il.append(tmp)

    elif decoded.op in [OP.JP, OP.JR]:
        if oper_type == OPER_TYPE.COND:
            append_conditional_jump(oper_val, operb_type, operb_val, addr + decoded.len, il)
        else:
            il.append(goto_or_jump(oper_type, oper_val, il))

    # elif decoded.op == OP.LD:
    #     assert len(decoded.operands) == 2

    #     if oper_type == OPER_TYPE.REG:
    #         size = REG_TO_SIZE[oper_val]
    #         # for two-byte nonzero loads, guess that it's an address
    #         if size == 2 and operb_type == OPER_TYPE.IMM and operb_val != 0:
    #             operb_type = OPER_TYPE.ADDR
    #         rhs = operand_to_il(operb_type, operb_val, il, size)
    #         set_reg = il.set_reg(size, reg2str(oper_val), rhs)
    #         il.append(set_reg)
    #     else:
    #         assert operb_type in [OPER_TYPE.REG, OPER_TYPE.IMM]

    #         if operb_type == OPER_TYPE.REG:
    #             # 1 or 2 byte stores are possible here:
    #             # ld (0xcdab),bc
    #             # ld (ix-0x55),a
    #             size = REG_TO_SIZE[operb_val]
    #         elif operb_type == OPER_TYPE.IMM:
    #             # only 1 byte stores are possible
    #             # eg: ld (ix-0x55),0xcd
    #             size = 1

    #         src = operand_to_il(operb_type, operb_val, il, size)
    #         dst = operand_to_il(oper_type, oper_val, il, size, peel_load=True)
    #         il.append(il.store(size, dst, src))

    elif decoded.op in [OP.LD, OP.LDI, OP.LDD]:
        expr = operand_to_il(operb_type, operb_val, il, size_hint=1)
        append_store_result(oper_type, oper_val, 1, expr, il)

    elif decoded.op in {OP.NOP, OP.DI, OP.EI, OP.HALT}:
        il.append(il.nop())

    elif decoded.op in {OP.STOP}:
        il.append(il.no_ret())

    elif decoded.op == OP.OR:
        tmp = il.reg(1, 'A')
        tmp = il.or_expr(1, operand_to_il(oper_type, oper_val, il, 1), tmp, flags='*')
        tmp = il.set_reg(1, 'A', tmp)
        il.append(tmp)

    elif decoded.op == OP.POP:
        # possible operands are: af bc de hl ix iy
        flag_write_type = '*' if oper_val == REG.AF else None

        size = REG_TO_SIZE[oper_val]
        tmp = il.pop(size)
        tmp = il.set_reg(size, reg2str(oper_val), tmp, flag_write_type)
        il.append(tmp)

    elif decoded.op == OP.PUSH:
        # possible operands are: af bc de hl ix iy

        # when pushing AF, actually push the flags
        if oper_val == REG.AF:
            # lo byte F first
            il.append(il.push(2,
                il.or_expr(
                    2,
                    il.or_expr(1,
                        il.or_expr(1,
                            il.shift_left(1, il.flag('z'), il.const(1, 7)),
                            il.shift_left(1, il.flag('n'), il.const(1, 6))
                        ),
                        il.or_expr(1,
                            il.shift_left(1, il.flag('h'), il.const(1, 5)),
                            il.shift_left(1, il.flag('c'), il.const(1, 4))
                        )
                    ),
                    il.shift_left(2,
                        il.reg(1, 'A'),
                        il.const(1, 8)
                    )
                )
            ))
        else:
            il.append(il.push( \
                REG_TO_SIZE[oper_val], \
                operand_to_il(oper_type, oper_val, il)))

    elif decoded.op in [OP.RL, OP.RLA]:
        # rotate THROUGH carry: b0=c, c=b8
        # LR35902 'RL' -> llil 'RLC'
        if decoded.op == OP.RLA:
            oper_type, oper_val = OPER_TYPE.REG, REG.A

        src = operand_to_il(oper_type, oper_val, il)
        rot = il.rotate_left_carry(1, src, il.const(1, 1), il.flag('c'), flags='c')
        append_store_result(oper_type, oper_val, 1, rot, il)

    elif decoded.op in [OP.RLC, OP.RLCA]:
        # rotate and COPY to carry: b0=c, c=b8
        # LR35902 'RL' -> llil 'ROL'
        if decoded.op == OP.RLCA:
            src = il.reg(1, 'A')
        else:
            src = operand_to_il(oper_type, oper_val, il)

        rot = il.rotate_left(1, src, il.const(1, 1), flags='c')

        append_store_result(oper_type or OPER_TYPE.REG, oper_val or REG.A, 1, rot, il)

    elif decoded.op == OP.SWAP:
        src = operand_to_il(oper_type, oper_val, il, size_hint=1)

        new_low = il.and_expr(1, il.logical_shift_right(1, src, il.const(1, 4)), il.const(1, 0xf))
        new_high = il.and_expr(1, il.shift_left(1, src, il.const(1, 4)), il.const(1, 0xf0))
        res = il.or_expr(1, new_low, new_high, flags='z')
        append_store_result(oper_type, oper_val, 1, res, il)

    elif decoded.op in {OP.RET, OP.RETI}:
        tmp = il.ret(il.pop(2))
        if decoded.operands:
            append_conditional_instr(decoded.operands[0][1], tmp, il)
        else:
            il.append(tmp)

    elif decoded.op in [OP.RR, OP.RRA]:
        # rotate THROUGH carry: b7=c, c=b0
        # LR35902 'RL' -> llil 'RRC'
        if decoded.op == OP.RRA:
            src = il.reg(1, 'A')
        else:
            src = operand_to_il(oper_type, oper_val, il, 1)

        rot = il.rotate_right_carry(1, src, il.const(1, 1), il.flag('c'), flags='c')

        if decoded.op == OP.RRA:
            il.append(il.set_reg(1, 'A', rot))
        elif oper_type == OPER_TYPE.REG:
            il.append(il.set_reg(1, reg2str(oper_val), rot))
        else:
            tmp2 = operand_to_il(oper_type, oper_val, il, 1, peel_load=True)
            il.append(il.store(1, tmp2, rot))

    elif decoded.op == OP.SRA:
        tmp = operand_to_il(oper_type, oper_val, il, 1)
        tmp = il.arith_shift_right(1, tmp, il.const(1, 1), flags='c')

        if oper_type == OPER_TYPE.REG:
            tmp = il.set_reg(1, reg2str(oper_val), tmp)
        else:
            tmp = il.store(1,
                operand_to_il(oper_type, oper_val, il, 1, peel_load=True),
                tmp
            )

        il.append(tmp)

    elif decoded.op == OP.SRL:
        tmp = operand_to_il(oper_type, oper_val, il, 1)
        tmp = il.logical_shift_right(1, tmp, il.const(1, 1), flags='c')

        if oper_type == OPER_TYPE.REG:
            tmp = il.set_reg(1, reg2str(oper_val), tmp)
        else:
            tmp = il.store(1,
                operand_to_il(oper_type, oper_val, il, 1, peel_load=True),
                tmp
            )

        il.append(tmp)

    elif decoded.op == OP.SUB:
        tmp = operand_to_il(oper_type, oper_val, il, 1)
        tmp = il.sub(1, il.reg(1, 'A'), tmp, flags='*')
        tmp = il.set_reg(1, 'A', tmp)
        il.append(tmp)

    elif decoded.op == OP.DEC:
        if oper_type == OPER_TYPE.REG:
            size = REG_TO_SIZE[oper_val]
            reg = operand_to_il(oper_type, oper_val, il, size)
            fwt = 'not_c' if size == 1 else None
            tmp = il.sub(size, reg, il.const(1, 1), flags=fwt)
            tmp = il.set_reg(size, reg2str(oper_val), tmp)
            il.append(tmp)
        else:
            mem = operand_to_il(oper_type, oper_val, il, 1)
            tmp = il.sub(1, mem, il.const(1, 1), flags='not_c')
            tmp = il.store(1, mem, tmp)
            il.append(tmp)

    elif decoded.op == OP.SBC:
        size = REG_TO_SIZE[oper_val]
        lhs = operand_to_il(oper_type, oper_val, il, size)
        rhs = operand_to_il(operb_type, operb_val, il, size)
        tmp = il.sub_borrow(size, lhs, rhs, il.flag('c'), flags='*')
        tmp = il.set_reg(1, 'A', tmp)
        il.append(tmp)

    elif decoded.op == OP.XOR:
        tmp = il.reg(1, 'A')
        tmp = il.xor_expr(1, operand_to_il(oper_type, oper_val, il, 1), tmp, flags='*')
        tmp = il.set_reg(1, 'A', tmp)
        il.append(tmp)

    else:
        print(f"unimplemented opcode lifter: {decoded2str(decoded)} @ {hex(addr)}")
        il.append(il.unimplemented())
        #il.append(il.nop()) # these get optimized away during lifted il -> llil

