#!/usr/bin/env python

import re

from binaryninja.log import log_info
from binaryninja.architecture import Architecture
from binaryninja.function import RegisterInfo, InstructionInfo, InstructionTextToken
from binaryninja.enums import InstructionTextTokenType, BranchType, FlagRole, LowLevelILFlagCondition

from . import LR35902IL

from lr35902dis.lr35902 import *

CC_TO_STR = {
    CC.ALWAYS:'1', CC.NOT_Z:'nz', CC.Z:'z',
    CC.NOT_C:'nc', CC.C:'c'
}

class LR35902(Architecture):
    name = 'LR35902'

    address_size = 2
    default_int_size = 1
    instr_alignment = 1
    max_instr_length = 4

    # register related stuff
    regs = {
        # main registers
        'AF': RegisterInfo('AF', 2),
        'BC': RegisterInfo('BC', 2),
        'DE': RegisterInfo('DE', 2),
        'HL': RegisterInfo('HL', 2),

        # main registers (sub)
        "A": RegisterInfo("AF", 1, 1),
        "F": RegisterInfo("AF", 1, 0),
        "B": RegisterInfo("BC", 1, 1),
        "C": RegisterInfo("BC", 1, 0),
        "D": RegisterInfo("DE", 1, 1),
        "E": RegisterInfo("DE", 1, 0),
        "H": RegisterInfo("HL", 1, 1),
        "L": RegisterInfo("HL", 1, 0),
        "Flags": RegisterInfo("AF", 0),

        # index registers
        'SP': RegisterInfo('SP', 2),

        # program counter
        'PC': RegisterInfo('PC', 2),

        # status
        # 'status': RegisterInfo('status', 1)
    }

    stack_pointer = "SP"

    # (address, name)
    IO_REGISTERS = {
        0xFF00: "P1",
        0xFF01: "SB",
        0xFF02: "SC",
        0xFF04: "DIV",
        0xFF05: "TIMA",
        0xFF06: "TMA",
        0xFF07: "TAC",
        0xFF0F: "IF",
        0xFF10: "NR10",
        0xFF11: "NR11",
        0xFF12: "NR12",
        0xff13: "NR13",
        0xFF14: "NR14",
        0xFF16: "NR21",
        0xFF17: "NR22",
        0xFF18: "NR23",
        0xFF19: "NR24",
        0xFF1A: "NR30",
        0xFF1B: "NR31",
        0xFF1C: "NR32",
        0xFF1D: "NR33",
        0xFF1E: "NR34",
        0xFF20: "NR41",
        0xFF21: "NR42",
        0xFF22: "NR43",
        0xFF23: "NR44",
        0xFF24: "NR50",
        0xFF25: "NR51",
        0xFF26: "NR52",
        0xFF40: "LCDC",
        0xFF41: "STAT",
        0xFF42: "SCY",
        0xFF43: "SCX",
        0xFF44: "LY",
        0xFF45: "LYC",
        0xFF46: "DMA",
        0xFF47: "BGP",
        0xFF48: "OBP0",
        0xFF49: "OBP1",
        0xFF4A: "WY",
        0xFF4B: "WX",
        0xFF4D: "KEY1",
        0xFF4F: "VBK",
        0xFF51: "HDMA1",
        0xFF52: "HDMA2",
        0xFF53: "HDMA3",
        0xFF54: "HDMA4",
        0xFF55: "HDMA5",
        0xFF56: "RP",
        0xFF68: "BCPS",
        0xFF69: "BCPD",
        0xFF6A: "OCPS",
        0xFF6B: "OCPD",
        0xFF70: "SVBK",
        0xFFFF: "IE",
    }

#------------------------------------------------------------------------------
# FLAG fun
#------------------------------------------------------------------------------

    flags = ['z', 'h', 'n', 'c']

    # remember, class None is default/integer
    semantic_flag_classes = ['class_bitstuff']

    # flag write types and their mappings
    flag_write_types = ['dummy', '*', 'c', 'z', 'not_c']
    flags_written_by_flag_write_type = {
        'dummy': [],
        '*': ['z', 'h', 'n', 'c'],
        'c': ['c'],
        'z': ['z'],
        'not_c': ['z', 'h', 'n'] # eg: LR35902's DEC
    }
    semantic_class_for_flag_write_type = {
        # by default, everything is type None (integer)
#        '*': 'class_integer',
#        'c': 'class_integer',
#        'z': 'class_integer',
#        'cszpv': 'class_integer',
#        'not_c': 'class_integer'
    }

    # groups and their mappings
    semantic_flag_groups = ['group_e', 'group_ne', 'group_lt']
    flags_required_for_semantic_flag_group = {
        'group_lt': ['c'],
        'group_e': ['z'],
        'group_ne': ['z']
    }
    flag_conditions_for_semantic_flag_group = {
        #'group_e': {None: LowLevelILFlagCondition.LLFC_E},
        #'group_ne': {None: LowLevelILFlagCondition.LLFC_NE}
    }

    # roles
    flag_roles = {
        'z': FlagRole.ZeroFlagRole,
        'h': FlagRole.HalfCarryFlagRole,
        'n': FlagRole.SpecialFlagRole, # set if last instruction was a subtraction (incl. CP)
        'c': FlagRole.CarryFlagRole
    }

    # MAP (condition x class) -> flags
    def get_flags_required_for_flag_condition(self, cond, sem_class):
        #LogDebug('incoming cond: %s, incoming sem_class: %s' % (str(cond), str(sem_class)))

        if sem_class == None:
            lookup = {
                # Z, zero flag for == and !=
                LowLevelILFlagCondition.LLFC_E: ['z'],
                LowLevelILFlagCondition.LLFC_NE: ['z'],
                # Z, zero flag for == and !=
                LowLevelILFlagCondition.LLFC_E: ['z'],
                LowLevelILFlagCondition.LLFC_NE: ['z'],
                # H, half carry for ???
                # P, parity for ???
                # s> s>= s< s<= done by sub and overflow test
                #if cond == LowLevelILFlagCondition.LLFC_SGT:
                #if cond == LowLevelILFlagCondition.LLFC_SGE:
                #if cond == LowLevelILFlagCondition.LLFC_SLT:
                #if cond == LowLevelILFlagCondition.LLFC_SLE:

                # C, for these
                LowLevelILFlagCondition.LLFC_UGE: ['c'],
                LowLevelILFlagCondition.LLFC_ULT: ['c']
            }

            if cond in lookup:
                return lookup[cond]

        return []

#------------------------------------------------------------------------------
# CFG building
#------------------------------------------------------------------------------

    def get_instruction_info(self, data, addr):
        decoded = decode(data, addr)

        # on error, return nothing
        if decoded.status == DECODE_STATUS.ERROR or decoded.len == 0:
            return None

        # on non-branching, return length
        result = InstructionInfo()
        result.length = decoded.len
        if decoded.typ != INSTRTYPE.JUMP_CALL_RETURN:
            return result

        # jp has several variations
        if decoded.op == OP.JP:
            (oper_type, oper_val) = decoded.operands[0]

            # jp pe,0xDEAD
            if oper_type == OPER_TYPE.COND:
                assert decoded.operands[1][0] == OPER_TYPE.ADDR
                result.add_branch(BranchType.TrueBranch, decoded.operands[1][1])
                result.add_branch(BranchType.FalseBranch, addr + decoded.len)
            # jp (hl)
            elif oper_type in [OPER_TYPE.REG_DEREF]:
                result.add_branch(BranchType.IndirectBranch)
            # jp 0xDEAD
            elif oper_type == OPER_TYPE.ADDR:
                result.add_branch(BranchType.UnconditionalBranch, oper_val)
            else:
                raise Exception('handling JP')

        # jr can be conditional
        elif decoded.op == OP.JR:
            (oper_type, oper_val) = decoded.operands[0]

            # jr c,0xdf07
            if oper_type == OPER_TYPE.COND:
                assert decoded.operands[1][0] == OPER_TYPE.ADDR
                result.add_branch(BranchType.TrueBranch, decoded.operands[1][1])
                result.add_branch(BranchType.FalseBranch, addr + decoded.len)
            # jr 0xdf07
            elif oper_type == OPER_TYPE.ADDR:
                result.add_branch(BranchType.UnconditionalBranch, oper_val)
            else:
                raise Exception('handling JR')

        # call can be conditional
        elif decoded.op == OP.CALL:
            (oper_type, oper_val) = decoded.operands[0]
            # call c,0xdf07
            if oper_type == OPER_TYPE.COND:
                assert decoded.operands[1][0] == OPER_TYPE.ADDR
                result.add_branch(BranchType.CallDestination, decoded.operands[1][1])
            # call 0xdf07
            elif oper_type == OPER_TYPE.ADDR:
                result.add_branch(BranchType.CallDestination, oper_val)
            else:
                raise Exception('handling CALL')

        # ret can be conditional
        elif decoded.op == OP.RET:
            if decoded.operands and decoded.operands[0][0] == OPER_TYPE.COND:
                # conditional returns dont' end block
                pass
            else:
                result.add_branch(BranchType.FunctionReturn)

        # ret from interrupts
        elif decoded.op == OP.RETI:
            result.add_branch(BranchType.FunctionReturn)

        return result

#------------------------------------------------------------------------------
# STRING building, disassembly
#------------------------------------------------------------------------------

    def reg2str(self, r):
        return reg2str(r)

# from api/python/function.py:
#
#        TextToken                  Text that doesn't fit into the other tokens
#        InstructionToken           The instruction mnemonic
#        OperandSeparatorToken      The comma or whatever else separates tokens
#        RegisterToken              Registers
#        IntegerToken               Integers
#        PossibleAddressToken       Integers that are likely addresses
#        BeginMemoryOperandToken    The start of memory operand
#        EndMemoryOperandToken      The end of a memory operand
#        FloatingPointToken         Floating point number
    def get_instruction_text(self, data, addr):
        decoded = decode(data, addr)
        if decoded.status != DECODE_STATUS.OK or decoded.len == 0:
            return None

        result = []

        # opcode
        result.append(InstructionTextToken( \
            InstructionTextTokenType.InstructionToken, decoded.op.name))

        # space for operand
        if decoded.operands:
            result.append(InstructionTextToken(InstructionTextTokenType.TextToken, ' '))

        # operands
        for i, operand in enumerate(decoded.operands):
            (oper_type, oper_val) = operand

            if oper_type == OPER_TYPE.REG:
                result.append(InstructionTextToken( \
                    InstructionTextTokenType.RegisterToken, self.reg2str(oper_val)))

            elif oper_type == OPER_TYPE.REG_DEREF:
                toks = [
                    (InstructionTextTokenType.BeginMemoryOperandToken, '('),
                    (InstructionTextTokenType.RegisterToken, self.reg2str(oper_val)),
                    (InstructionTextTokenType.EndMemoryOperandToken, ')'),
                ]
                result.extend([InstructionTextToken(*ts) for ts in toks])

            elif oper_type in {OPER_TYPE.REG_DEREF_DEC, OPER_TYPE.REG_DEREF_INC}:
                update = '-' if oper_type == OPER_TYPE.REG_DEREF_DEC else '+'

                toks = [
                    (InstructionTextTokenType.BeginMemoryOperandToken, '('),
                    (InstructionTextTokenType.RegisterToken, self.reg2str(oper_val)),
                    (InstructionTextTokenType.TextToken, update),
                    (InstructionTextTokenType.EndMemoryOperandToken, ')'),
                ]
                result.extend([InstructionTextToken(*ts) for ts in toks])

            elif oper_type in {OPER_TYPE.REG_DEREF_FF00}:
                toks = [
                    (InstructionTextTokenType.BeginMemoryOperandToken, '('),
                    (InstructionTextTokenType.PossibleAddressToken, '0xFF00', 0xFF00),
                    (InstructionTextTokenType.TextToken, '+'),
                    (InstructionTextTokenType.RegisterToken, self.reg2str(oper_val)),
                    (InstructionTextTokenType.EndMemoryOperandToken, ')'),
                ]
                result.extend([InstructionTextToken(*ts) for ts in toks])

            elif oper_type == OPER_TYPE.ADDR:
                oper_val = oper_val & 0xFFFF
                txt = '0x%04x' % oper_val
                result.append(InstructionTextToken( \
                    InstructionTextTokenType.PossibleAddressToken, txt, oper_val))

            elif oper_type == OPER_TYPE.ADDR_DEREF:
                txt = '0x%04x' % oper_val
                toks = [
                    (InstructionTextTokenType.BeginMemoryOperandToken, '('),
                    (InstructionTextTokenType.PossibleAddressToken, txt, oper_val),
                    (InstructionTextTokenType.EndMemoryOperandToken, ')'),
                ]
                result.extend([InstructionTextToken(*ts) for ts in toks])

            elif oper_type == OPER_TYPE.ADDR_DEREF_FF00:
                txt = '0x{:02x}'.format(oper_val & 0xff)
                toks = [
                    (InstructionTextTokenType.BeginMemoryOperandToken, '('),
                    (InstructionTextTokenType.PossibleAddressToken, '0xFF00', 0xFF00),
                    (InstructionTextTokenType.TextToken, '+'),
                    (InstructionTextTokenType.IntegerToken, self.reg2str(oper_val)),
                    (InstructionTextTokenType.EndMemoryOperandToken, ')'),
                ]
                result.extend([InstructionTextToken(*ts) for ts in toks])

            elif oper_type == OPER_TYPE.IMM:
                if oper_val == 0:
                    txt = '0'
                elif oper_val >= 16:
                    txt = '0x%x' % oper_val
                else:
                    txt = '%d' % oper_val

                result.append(InstructionTextToken( \
                    InstructionTextTokenType.IntegerToken, txt, oper_val))

            elif oper_type == OPER_TYPE.COND:
                txt = CC_TO_STR[oper_val]
                result.append(InstructionTextToken( \
                    InstructionTextTokenType.TextToken, txt))

            elif oper_type == OPER_TYPE.SP_OFFSET:
                offset = '{:+02x}'.format(oper_val)
                sign, offset = offset[0], offset[1:]

                toks = [
                    (InstructionTextTokenType.BeginMemoryOperandToken, '('),
                    (InstructionTextTokenType.RegisterToken, 'SP'),
                    (InstructionTextTokenType.TextToken, sign),
                    (InstructionTextTokenType.IntegerToken, offset, abs(oper_val)),
                    (InstructionTextTokenType.EndMemoryOperandToken, ')'),
                ]
                result.extend([InstructionTextToken(*ts) for ts in toks])

            else:
                raise Exception('unknown operand type: ' + str(oper_type))

            # if this isn't the last operand, add comma
            if i < len(decoded.operands)-1:
                result.append(InstructionTextToken( \
                    InstructionTextTokenType.OperandSeparatorToken, ','))

        return result, decoded.len

#------------------------------------------------------------------------------
# LIFTING
#------------------------------------------------------------------------------

    def get_flag_write_low_level_il(self, op, size, write_type, flag, operands, il):
        flag_il = LR35902IL.gen_flag_il(op, size, write_type, flag, operands, il)
        if flag_il:
            return flag_il

        return Architecture.get_flag_write_low_level_il(self, op, size, write_type, flag, operands, il)

    def get_instruction_low_level_il(self, data, addr, il):
        decoded = decode(data, addr)
        if decoded.status != DECODE_STATUS.OK or decoded.len == 0:
            return None

        LR35902IL.gen_instr_il(addr, decoded, il)

        return decoded.len

