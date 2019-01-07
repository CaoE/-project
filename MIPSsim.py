
import sys
import argparse
class FuStatus(object):
    def __init__(self):
        self.preMemStatu = []
        self.preAluStatu = []
        self.preAlubStatu = []
        for i in range(0,2):
            entry = {"name": "", "busy": False, "Op": "", "Ri": "", "Rj": "", "Rk": "", "Qj": "", "Qj": "", "RYj": True,
                     "RYk": True}
            self.preMemStatu.append(entry)
        for i in range(0,2):
            entry = {"name": "", "busy": False, "Op": "", "Fi": "", "Fj": "", "Fk": "", "Qj": "", "Qj": "", "RYj": True,
                     "RYk": True}
            self.preAluStatu.append(entry)
        for i in range(0, 2):
            entry = {"name": "", "busy": False, "Op": "", "Fi": "", "Fj": "", "Fk": "", "Qj": "", "Qj": "", "RYj": True,
                     "RYk": True}
            self.preAlubStatu.append(entry)




class ScoreBoarding(object):
    def __init__(self):
        self.fu_status = FuStatus()
        #self.reg_status = RegResultStatus()
        self.reg_status ={}
        for i in range(0,32):
            head = "R%d" % i
            self.reg_status.update({head:""})

        self.if_statu = {}
        entry = {"wait":""}
        self.if_statu.update(entry)
        entry = {"exec":""}
        self.if_statu.update(entry)

        self.fetch_inst = {}

        self.pre_issue = {}
        self.pre_mem = {}
        self.pre_alu = {}
        self.pre_alub = {}

        self.post_mem = {"result":"", "inst":""}
        self.post_alu = {"result":"", "inst":""}
        self.post_alub = {"result":"", "inst":""}



class MIPS(object):
    def __init__(self,inputFile, disassemblyFile,simulationFile):
        self.input = inputFile
        self.disassemblyFile = disassemblyFile;
        self.simulationFile = simulationFile
        self.mipsScoreBoarding = ScoreBoarding()
        self.count = 0
        self.__codeStart = 64
        self.__indicator = 0
        self.__instLen = 4
        self.__dataStart = 0
        self.__dataEnd = 0
        self.__writeData = ""
        self.__writeSim = ""
        self.__pc = 0
        self.__instSegment = {}
        self.__dataSegment = {}
        self.__regFlie = [0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0,
                          0,0,0,0,0,0,0,0]
    def write_file(self, output, file_path):
        try:
            f = open(file_path, "w")
        except:
            print "Can not open file."
            sys.exit(1)
        try:
            f.write(output)
        except:
            print "Can not write file."
            sys.exit(1)
        finally:
            f.close()

    @staticmethod
    def format_opAND_ADD_NOR_SLT_MUL_SUB(inst):
        if(inst[0] == "0"):
            return (int(inst[16:21], 2), int(inst[6:11], 2), "R", int(inst[11:16], 2))
        else:
            return (int(inst[11:16], 2),int(inst[6:11], 2),  "#", int(inst[16:32], 2))


    @staticmethod
    def format_opSLL_SRL_SRA_MULI(inst):
        if(inst[26:32] == "000010" and inst[0:6] == "000000"):
            return ("SRL",int(inst[16:21], 2), int(inst[11:16], 2), int(inst[21:26], 2))
        if(inst[26:32] == "000011" and inst[0:6] == "000000"):
            return ("SRA", int(inst[16:21], 2), int(inst[11:16], 2), int(inst[21:26], 2))
        if(inst[0:6] == "100001"):
            return ("MUL", int(inst[11:16], 2),int(inst[6:11], 2),  int(inst[16:32], 2))
        if(inst[26:32] == "000000" and inst[0:6] == "000000"):
            return (int(inst[16:21], 2), int(inst[11:16], 2), int(inst[21:26], 2))

    @staticmethod
    def format_opJR(inst):
        return (int(inst[6:11], 2))

    @staticmethod
    def format_opJ(inst):
        return 4*int(inst[6:32], 2)


    @staticmethod
    def format_opSWLW(inst):
        return (int(inst[11:16], 2), int(inst[16:32], 2), int(inst[6:11], 2))

    @staticmethod
    def format_opBEQ(inst):
        return (int(inst[6:11], 2), int(inst[11:16], 2), 4*int(inst[16:32], 2))

    @staticmethod
    def format_opBTZ(inst):
        return (int(inst[6:11], 2), 4*int(inst[16:32], 2))

    switch_function_special = {
        #move last bit
        "10000": lambda instruction:"ADD R%d, R%d, %s%d" % MIPS.format_opAND_ADD_NOR_SLT_MUL_SUB(instruction),     #2
        "00100": lambda instruction:"JR R%d"            % MIPS.format_opJR(instruction),
        "10001": lambda instruction:"SUB R%d, R%d, %s%d" % MIPS.format_opAND_ADD_NOR_SLT_MUL_SUB(instruction),     #2
        "00000": lambda instruction:"SLL R%d, R%d, #%d" % MIPS.format_opSLL_SRL_SRA_MULI(instruction),   #SLL NOP
        "00001": lambda instruction: "%s R%d, R%d, #%d" % MIPS.format_opSLL_SRL_SRA_MULI(instruction),
        "10010": lambda instruction:"AND R%d, R%d, %s%d" % MIPS.format_opAND_ADD_NOR_SLT_MUL_SUB(instruction),
        "10011": lambda instruction:"NOR R%d, R%d, %s%d" % MIPS.format_opAND_ADD_NOR_SLT_MUL_SUB(instruction),
        "10101": lambda instruction:"SLT R%d, R%d, %s%d" % MIPS.format_opAND_ADD_NOR_SLT_MUL_SUB(instruction),
        "01011": lambda instruction: "SW R%d, %d(R%d)"  % MIPS.format_opSWLW(instruction),
        "00011": lambda instruction: "LW R%d, %d(R%d)"  % MIPS.format_opSWLW(instruction),
        "00110": lambda instruction: "BREAK"
    }
    switch_instruction = {
        "000000": lambda instruction: MIPS.switch_function_special[instruction[26:31]](instruction),
        "000010": lambda instruction: "J #%d" %MIPS.format_opJ(instruction),
        "000100": lambda instruction: "BEQ R%d, R%d, #%d" % MIPS.format_opBEQ(instruction),
        "000111": lambda instruction: "BGTZ R%d, #%d" % MIPS.format_opBTZ(instruction),
        "000001": lambda instruction: "BLTZ R%d, #%d" % MIPS.format_opBTZ(instruction),
        "011100": lambda instruction: "MUL R%d, R%d, %s%d" % MIPS.format_opAND_ADD_NOR_SLT_MUL_SUB(instruction)
        #"101011": lambda instruction: "SW R%d, %d(R%d)" % MIPS.format_op5(instruction),
        #"100011": lambda instruction: "LW R%d, %d(R%d)" % MIPS.format_op5(instruction),
    }
    switch_first = {
        "0": lambda instruction: MIPS.switch_instruction[instruction[0:6]](instruction),
        "1": lambda instruction: MIPS.switch_function_special[instruction[1:6]](instruction)
    }



    def analyse_instructions(self, code):
        if(code[0:32] == "00000000000000000000000000000000"):
            disassembledData = "NOP"
        else:
            disassembledData = MIPS.switch_first[code[0:1]](code)
        #print disassembledData
        return disassembledData

    def analyse_data(self, code):
        if code[0] == "0":
            return int(code[:], 2)
        else:
            conv = ""
            for bit in code[:]:
                if bit == "0":
                    conv += "1"
                elif bit == "1":
                    conv += "0"
            return -(int(conv, 2)+1)



    def disassemble(self):
        try:
            binaryFile = open(self.input, "r")
        except:
            print "Can not open"
            sys.exit(1)
        try:
            codes = binaryFile.read()
        except:
            print "Can not read"
            sys.exit(1)
        finally:
            binaryFile.close()
        codes = codes.split('\n')
        self.__indicator = self.__codeStart
        flag = False
        for codeLine in codes:
            if flag == False:
                split1, split12, split13, split14, split15, split16 = \
                    codeLine[0:6], codeLine[6:11], codeLine[11:16], codeLine[16:21], codeLine[21:26], codeLine[26:32]
                inst = self.analyse_instructions(codeLine)
                self.__instSegment[self.__indicator] = inst
                self.__writeData += split1 + " " + split12 + " " + split13+ " " +split14+ " " +split15+ " " +split16
                self.__writeData +="\t" + `self.__indicator`+ "\t" + inst + "\n"
                self.__indicator += self.__instLen

                if inst == "BREAK":
                    flag = True
                    self.__dataStart =  self.__indicator
            else:
                data = self.analyse_data(codeLine)
                self.__dataSegment[self.__indicator] = data
                self.__writeData += codeLine + `self.__indicator`+"\t" + `data`+"\n"
                self.__indicator += self.__instLen
        self.__dataEnd = self.__indicator
        print self.__writeData
        self.write_file(self.__writeData, self.disassemblyFile)
    @staticmethod
    def exeSRL(rt, sa):
        global cbit
        cbit = 0
        data = '{:032b}'.format(rt)

        if data[0] == "0":
            return rt >> sa
        else:
            cdata = "1"
            for bit in data[1:]:
                if bit == "0":
                    cdata += "1"
                else:
                    cdata += "0"
            copydata = list(cdata)
            for i in range(31, -1, -1):
                if i == 31:
                    if cdata[i] == "1":
                        cbit = 1
                        copydata[i] = "0"
                elif cbit == 1:
                    if cdata[i] == "1":
                        cbit = 1
                        copydata[i] = "0"
                    else:
                        cbit = 0
                        copydata[i] = "1"
            copydata = ''.join(copydata)
            finaldata = ""
            for i in range(sa):
                finaldata += "0"
            for bit in copydata[:-sa]:
                finaldata += bit
            return (int(finaldata, 2))

    execute_inst = {

        "ADD": lambda op2,op3 : op2 + op3,
        "SUB": lambda op2,op3: op2 - op3,
        #"BREAK": lambda
        #"SW": lambda rt, offset:
        #"LW":
        "SLL": lambda rt, sa: rt << sa,
        "SRL": lambda inst, sa: MIPS.exeSRL(inst, sa),
        "SRA": lambda rt, sa: rt >> sa,
        #"NOP":
        "MUL": lambda op2, op3: op2 * op3,
        "AND": lambda op2, op3: op2 & op3,
        "NOR": lambda op2, op3: op2 ^ op3,
        "SLT": lambda op2, op3: op2 < op3
    }

    def IF(self,fetched_list):
        if self.mipsScoreBoarding.if_statu["exec"] != "":
            inst = self.mipsScoreBoarding.if_statu["exec"]
            op = inst.replace(",", "").split(" ")
            if op[0] == "J":
                target = int(op[1].replace("#", ""))
                self.__pc = target
                self.mipsScoreBoarding.if_statu["exec"] = ""
            elif op[0] == "JR":
                op1 = int(op[1].replace("R", ""))
                self.__pc = self.__regFlie[op1]
                self.mipsScoreBoarding.if_statu["exec"] = ""
            elif op[0] == "BEQ":
                op1 = int(op[1].replace("R", ""))
                op2 = int(op[2].replace("R", ""))
                if self.__regFlie[op1] == self.__regFlie[op2]:
                    offset = int(op[3].replace("#", ""))
                    self.__pc += offset
                self.mipsScoreBoarding.if_statu["exec"] = ""
            elif op[0] == "BLTZ":
                op1 = int(op[1].replace("R", ""))
                if self.__regFlie[op1] < 0:
                    offset = int(op[2].replace("#", ""))
                    self.__pc += offset
                self.mipsScoreBoarding.if_statu["exec"] = ""
            elif op[0] == "BGTZ":
                op1 = int(op[1].replace("R", ""))
                if self.__regFlie[op1] > 0:
                    offset = int(op[2].replace("#", ""))
                    self.__pc += offset
                self.mipsScoreBoarding.if_statu["exec"] = ""
            elif op[0] == "BREAK":
                self.mipsScoreBoarding.if_statu["exec"] = ""
            elif op[0] == "NOP":
                self.mipsScoreBoarding.if_statu["exec"] = ""

        elif self.mipsScoreBoarding.if_statu["wait"] != "":
            inst = self.mipsScoreBoarding.if_statu["wait"]
            op = inst.replace(",", "").split(" ")
            rawflag = False
            if op[0] == "JR":
                if self.mipsScoreBoarding.reg_status[op[1]] != "":  #
                    rawflag = True
                for kry, prei in self.mipsScoreBoarding.pre_issue.items():
                    preop = prei.replace(",", "").split(" ")
                    if preop[0] != "SW":
                        if preop[1] == op[1]:
                            rawflag = True
                if rawflag == False:
                    self.mipsScoreBoarding.if_statu["exec"] = inst
                    self.mipsScoreBoarding.if_statu["wait"] = ""
            elif op[0] == "BEQ":
                if self.mipsScoreBoarding.reg_status[op[1]] != "" or self.mipsScoreBoarding.reg_status[op[2]] != "":
                    rawflag = True
                for kry, prei in self.mipsScoreBoarding.pre_issue.items():
                    preop = prei.replace(",", "").split(" ")
                    if preop[0] != "SW":
                        if preop[1] == op[1] or preop[1] == op[2]:
                            rawflag = True
                if rawflag == False:
                    self.mipsScoreBoarding.if_statu["exec"] = inst
                    self.mipsScoreBoarding.if_statu["wait"] = ""
            elif op[0] == "BLTZ":
                if self.mipsScoreBoarding.reg_status[op[1]] != "":
                    rawflag = True
                for kry, prei in self.mipsScoreBoarding.pre_issue.items():
                    preop = prei.replace(",", "").split(" ")
                    if preop[0] != "SW":
                        if preop[1] == op[1]:
                            rawflag = True
                if rawflag == False:
                    self.mipsScoreBoarding.if_statu["exec"] = inst
                    self.mipsScoreBoarding.if_statu["wait"] = ""
            elif op[0] == "BGTZ":
                if self.mipsScoreBoarding.reg_status[op[1]] != "":
                    rawflag = True
                for kry, prei in self.mipsScoreBoarding.pre_issue.items():
                    preop = prei.replace(",", "").split(" ")
                    if preop[0] != "SW":
                        if preop[1] == op[1]:
                            rawflag = True
                if rawflag == False:
                    self.mipsScoreBoarding.if_statu["exec"] = inst
                    self.mipsScoreBoarding.if_statu["wait"] = ""
            return
        if self.mipsScoreBoarding.if_statu["exec"] == "" and self.mipsScoreBoarding.if_statu["wait"] == "":

            for i in range(0, 2):
                if len(self.mipsScoreBoarding.pre_issue) + len(fetched_list) >= 4:
                    break

                nowInst = self.__instSegment[self.__pc]
                op = nowInst.replace(",", "").split(" ")
                self.__pc += self.__instLen;

                rawflag2 = False

                if op[0] == "J":
                    # target = int(op[1].replace("#", ""))
                    self.mipsScoreBoarding.if_statu["exec"] = nowInst
                    break
                    # self.__pc = target
                elif op[0] == "JR":
                    # op1 = int(op[1].replace("R", ""))
                    if self.mipsScoreBoarding.reg_status[op[1]] != "":
                        rawflag2 = True
                        #self.mipsScoreBoarding.if_statu["exec"] = nowInst
                        # op1 = int(op[1].replace("R", ""))
                        # self.__pc = self.__regFlie[op1]
                    for kry, prei in self.mipsScoreBoarding.pre_issue.items():
                        preop = prei.replace(",", "").split(" ")
                        if preop[0] != "SW":
                            if preop[1] == op[1]:
                                rawflag2 = True
                    if rawflag2 == False:
                        self.mipsScoreBoarding.if_statu["exec"] = nowInst
                    else:
                        self.mipsScoreBoarding.if_statu["wait"] = nowInst
                    break

                elif op[0] == "BEQ":
                    if self.mipsScoreBoarding.reg_status[op[1]] != "" or self.mipsScoreBoarding.reg_status[op[2]] != "":
                        rawflag2 = True
                        #self.mipsScoreBoarding.if_statu["exec"] = nowInst
                        # op1 = int(op[1].replace("R", ""))
                        # op2 = int(op[2].replace("R", ""))
                        # if self.__regFlie[op1] == self.__regFlie[op2]:
                        #    offset = int(op[3].replace("#", ""))
                        #    self.__pc += offset
                    for kry, prei in self.mipsScoreBoarding.pre_issue.items():
                        preop = prei.replace(",", "").split(" ")
                        if preop[0] != "SW":
                            if preop[1] == op[1] or preop[1] == op[2]:
                                rawflag2 = True
                    if rawflag2 == False:
                        self.mipsScoreBoarding.if_statu["exec"] = nowInst
                    else:
                        self.mipsScoreBoarding.if_statu["wait"] = nowInst
                    break
                elif op[0] == "BLTZ":
                    if self.mipsScoreBoarding.reg_status[op[1]] != "":
                        rawflag2 = True
                        #self.mipsScoreBoarding.if_statu["exec"] = nowInst
                        # op1 = int(op[1].replace("R", ""))
                        # if self.__regFlie[op1] < 0:
                        #    offset = int(op[2].replace("#", ""))
                        #    self.__pc += offset
                    for kry, prei in self.mipsScoreBoarding.pre_issue.items():
                        preop = prei.replace(",", "").split(" ")
                        if preop[0] != "SW":
                            if preop[1] == op[1]:
                                rawflag2 = True
                    if rawflag2 == False:
                        self.mipsScoreBoarding.if_statu["exec"] = nowInst
                    else:
                        self.mipsScoreBoarding.if_statu["wait"] = nowInst
                    break
                elif op[0] == "BGTZ":
                    if self.mipsScoreBoarding.reg_status[op[1]] != "":
                        rawflag2 = True
                        #self.mipsScoreBoarding.if_statu["exec"] = nowInst
                        # op1 = int(op[1].replace("R", ""))
                        # if self.__regFlie[op1] > 0:
                        #    offset = int(op[2].replace("#", ""))
                        #    self.__pc += offset
                    for kry, prei in self.mipsScoreBoarding.pre_issue.items():
                        preop = prei.replace(",", "").split(" ")
                        if preop[0] != "SW":
                            if preop[1] == op[1]:
                                rawflag2 = True
                    if rawflag2 == False:
                        self.mipsScoreBoarding.if_statu["exec"] = nowInst
                    else:
                        self.mipsScoreBoarding.if_statu["wait"] = nowInst
                    break
                elif op[0] == "BREAK":
                    self.mipsScoreBoarding.if_statu["exec"] = nowInst
                    break
                elif op[0] == "NOP":
                    self.mipsScoreBoarding.if_statu["exec"] = nowInst
                    break
                else:
                    fetched_list.append(nowInst)






            #else:
            #    self.__pc -= self.__instLen;







    def Issue(self,pre_mem,pre_alu,pre_alub):
        keytodeletelist = []
        if len(self.mipsScoreBoarding.pre_issue) > 0:


            for key, value in self.mipsScoreBoarding.pre_issue.items():
                WarHazard = False
                WawHazard = False
                RawHazard = False
                MemOrderHazard = False
                issueLW = False
                op = value.replace(",", "").split(" ")
                if op[0] in ("ADD", "AND", "SUB", "NOR"):

                    if len(self.mipsScoreBoarding.pre_alu) < 2:#
                        if len(pre_alu) >= 2 - len(self.mipsScoreBoarding.pre_alu):
                            break
                        # Check WAR with earlier not-issued inst
                        for i in range(0,key):
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if preop[0] not in ("SW","LW"):
                                if preop[2] == op[1] or  preop[3] == op[1]:
                                    WarHazard = True
                            else:
                                if preop[0] == "SW":
                                    num = preop[2].split("(")
                                    basereg = num[1].replace(")", "")
                                    if preop[1] == op[1] or basereg == op[1]:
                                        WarHazard = True
                                else:
                                    num = preop[2].split("(")
                                    basereg = num[1].replace(")", "")
                                    if basereg == op[1]:
                                        WarHazard = True


                        # Check WAW with pre and issued
                        if self.mipsScoreBoarding.reg_status[op[1]] != "" :
                            WawHazard = True
                        for i in range(0, key):
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if preop[1] == op[1]:
                                WawHazard = True

                        # Check Raw
                        # issued
                        if op[2].find("R") != -1:
                            if self.mipsScoreBoarding.reg_status[op[2]] != "":
                                RawHazard = True
                        if op[3].find("R") != -1:
                            if self.mipsScoreBoarding.reg_status[op[3]] != "":
                                RawHazard = True
                        # pre not issued
                        for i in range(0, key):
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if preop[1] == op[2] or preop[1] == op[3]:
                                RawHazard = True

                        if WarHazard == False and RawHazard ==False and WawHazard == False:
                            pre_alu.append(value)
                            keytodeletelist.append(key)
                            #self.mipsScoreBoarding.pre_issue.pop(key)

                elif op[0] in ("SLL", "SRL", "SRA", "MUL"):
                    if len(self.mipsScoreBoarding.pre_alub) < 2:#
                        if len(pre_alub) >= 2 - len(self.mipsScoreBoarding.pre_alub):
                            break
                        # Check WAR with earlier not-issued inst
                        for i in range(0,key):
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if preop[0] not in ("SW","LW"):
                                if preop[2] == op[1] or  preop[3] == op[1]:
                                    WarHazard = True
                            else:
                                if preop[0] == "SW":
                                    num = preop[2].split("(")
                                    basereg = num[1].replace(")", "")
                                    if preop[1] == op[1] or basereg == op[1]:
                                        WarHazard = True
                                else:
                                    num = preop[2].split("(")
                                    basereg = num[1].replace(")", "")
                                    if basereg == op[1]:
                                        WarHazard = True

                        # Check WAW with pre and issued
                        if self.mipsScoreBoarding.reg_status[op[1]] != "":
                            WawHazard = True
                        for i in range(0, key):
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if preop[1] == op[1]:
                                WawHazard = True

                        # Check Raw
                        # issued
                        if op[2].find("R") != -1:
                            if self.mipsScoreBoarding.reg_status[op[2]] != "":
                                RawHazard = True

                        # pre not issued
                        for i in range(0, key):
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if preop[1] == op[2]:
                                RawHazard = True
                        if WarHazard == False and RawHazard ==False and WawHazard == False:
                            pre_alub.append(value)
                            keytodeletelist.append(key)
                            #self.mipsScoreBoarding.pre_issue.pop(key)

                elif op[0] in ("SW", "LW"):
                    if len(self.mipsScoreBoarding.pre_mem) < 2:#
                        if len(pre_mem) >= 2 - len(self.mipsScoreBoarding.pre_mem):
                            break
                        
                        # all source are ready / RAW
                        num = op[2].split("(")
                        basereg = num[1].replace(")", "")

                        if op[0] == "LW":
                            if self.mipsScoreBoarding.reg_status[basereg] != "":
                                RawHazard = True
                        else:
                            if self.mipsScoreBoarding.reg_status[op[1]] != "" or self.mipsScoreBoarding.reg_status[basereg] != "":
                                RawHazard = True
                        for i in range(0, key):
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if op[0] == "LW":
                                if preop[0] != "SW":
                                    if preop[1] == basereg:
                                        RawHazard = True
                            else:
                                if preop[1] == op[1] or preop[1] == basereg:
                                    RawHazard = True

                        # Check WAR with earlier not-issued inst
                        for i in range(0,key):
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if preop[0] not in ("SW","LW"):
                                if op[0] =="LW":
                                    if preop[2] == op[1] or  preop[3] == op[1]:
                                        WarHazard = True

                            else:
                                if preop[0] == "LW":
                                    if op[0] == "LW":
                                        num = preop[2].split("(")
                                        basereg = num[1].replace(")", "")
                                        if op[1] == basereg:
                                            WarHazard = True

                        # Check WAW with pre and issued
                        if op[0] == "LW":
                            if self.mipsScoreBoarding.reg_status[op[1]] != "":
                                WawHazard = True
                            for i in range(0, key):
                                preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                                if preop[0] != "SW":
                                    if preop[1] == op[1]:
                                        WawHazard = True

                        # Check mem order
                        for i in range(0, key):#
                            preop = self.mipsScoreBoarding.pre_issue[i].replace(",", "").split(" ")
                            if preop[0] == "SW":
                                MemOrderHazard = True
                                if op[0] == "LW":
                                    issueLW = True

                        if WarHazard == False and RawHazard ==False and WawHazard == False and MemOrderHazard ==False:
                            pre_mem.append(value)
                            keytodeletelist.append(key)
                        elif WarHazard == False and RawHazard ==False and WawHazard == False and MemOrderHazard ==True and issueLW==True:
                            pre_mem.append(value)
                            keytodeletelist.append(key)

        #remove issued inst
        for key in keytodeletelist:
            inst = self.mipsScoreBoarding.pre_issue[key]
            op = inst.replace(",", "").split(" ")
            if op[0] != "SW":
                self.mipsScoreBoarding.reg_status[op[1]] = "take"
            self.mipsScoreBoarding.pre_issue.pop(key)

        #resort issued inst
        index = 0
        for key in self.mipsScoreBoarding.pre_issue:
            self.mipsScoreBoarding.pre_issue.update({index: self.mipsScoreBoarding.pre_issue.pop(key)})
            index += 1





    #def ReadOp(self):
    def Execution(self,post_alu,post_alub,post_mem):
        if len(self.mipsScoreBoarding.pre_alu) > 0:# 1 cycle
            inst = self.mipsScoreBoarding.pre_alu[0]
            op = inst.replace(",", "").split(" ")
            op1 = int(op[1].replace("R", ""))
            op2 = int(op[2].replace("R", ""))
            if op[3][0] == '#':
                op3 = int(op[3].replace("#", ""))
                post_alu["result"] = MIPS.execute_inst[op[0]](self.__regFlie[op2], op3)

            else:
                op3 = int(op[3].replace("R", ""))
                post_alu["result"] = MIPS.execute_inst[op[0]](self.__regFlie[op2], self.__regFlie[op3])
            post_alu["inst"] = inst
            self.mipsScoreBoarding.pre_alu.pop(0)
            if len(self.mipsScoreBoarding.pre_alu) > 0:
                self.mipsScoreBoarding.pre_alu.update({0: self.mipsScoreBoarding.pre_alu.pop(1)})

        if len(self.mipsScoreBoarding.pre_alub) > 0:#2 cycle
            if self.count == 1:
                inst = self.mipsScoreBoarding.pre_alub[0]
                op = inst.replace(",", "").split(" ")
                op1 = int(op[1].replace("R", ""))
                op2 = int(op[2].replace("R", ""))
                if op[0] != "MUL":
                    op3 = int(op[3].replace("#", ""))
                    post_alub["result"]= MIPS.execute_inst[op[0]](self.__regFlie[op2], op3)

                else:
                    if op[3][0] == '#':
                        op3 = int(op[3].replace("#", ""))
                        post_alub["result"] = MIPS.execute_inst[op[0]](self.__regFlie[op2], op3)

                    else:
                        op3 = int(op[3].replace("R", ""))
                        post_alub["result"] = MIPS.execute_inst[op[0]](self.__regFlie[op2], self.__regFlie[op3])
                post_alub["inst"] = inst
                self.count = 0
                self.mipsScoreBoarding.pre_alub.pop(0)
                if len(self.mipsScoreBoarding.pre_alub) > 0:
                    self.mipsScoreBoarding.pre_alub.update({0: self.mipsScoreBoarding.pre_alub.pop(1)})
            else:
                self.count += 1

        if len(self.mipsScoreBoarding.pre_mem) > 0:#1 cycle
            inst = self.mipsScoreBoarding.pre_mem[0]
            op = inst.replace(",", "").split(" ")
            op1 = int(op[1].replace("R", ""))
            num = op[2].split("(")
            offset = int(num[0])
            b = num[1].replace(")", "")
            basereg = int(b.replace("R", ""))
            if op[0] == "LW":
                post_mem["result"] = self.__dataSegment[self.__regFlie[basereg] + offset]
                post_mem["inst"] = inst
            elif op[0] == "SW":
                self.__dataSegment[self.__regFlie[basereg] + offset] = self.__regFlie[op1]

            self.mipsScoreBoarding.pre_mem.pop(0)
            if len(self.mipsScoreBoarding.pre_mem) > 0:
                self.mipsScoreBoarding.pre_mem.update({0: self.mipsScoreBoarding.pre_mem.pop(1)})


    def WriteResult(self):
        if self.mipsScoreBoarding.post_alu["result"]!="" :
            inst =self.mipsScoreBoarding.post_alu["inst"]
            result = int(self.mipsScoreBoarding.post_alu["result"])
            op = inst.replace(",", "").split(" ")
            op1 = int(op[1].replace("R", ""))
            self.__regFlie[op1] = result
            self.mipsScoreBoarding.reg_status[op[1]] = ""
        if self.mipsScoreBoarding.post_alub["result"]!="" :
            inst =self.mipsScoreBoarding.post_alub["inst"]
            result = int(self.mipsScoreBoarding.post_alub["result"])
            op = inst.replace(",", "").split(" ")
            op1 = int(op[1].replace("R", ""))
            self.__regFlie[op1] = result
            self.mipsScoreBoarding.reg_status[op[1]] = ""
        if self.mipsScoreBoarding.post_mem["result"]!="" :
            inst =self.mipsScoreBoarding.post_mem["inst"]
            result = int(self.mipsScoreBoarding.post_mem["result"])
            op = inst.replace(",", "").split(" ")
            op1 = int(op[1].replace("R", ""))
            self.__regFlie[op1] = result
            self.mipsScoreBoarding.reg_status[op[1]] = ""

    def print_simInfo(self, cycle):
        siminfo = "--------------------\nCycle:%d\n\n" % cycle
        nowInst = self.mipsScoreBoarding.if_statu["wait"]
        op = nowInst.replace(",", "").split(" ")
        opname = op[0] + "\t"
        reformInst1 = nowInst.replace(op[0] + " ", opname)
        nowInst = self.mipsScoreBoarding.if_statu["exec"]
        op = nowInst.replace(",", "").split(" ")
        opname = op[0] + "\t"
        reformInst2 = nowInst.replace(op[0] + " ", opname)
        siminfo += "IF Unit:\n\tWaiting Instruction: %s\n\tExecuted Instruction: %s\n" % (reformInst1,reformInst2)
        siminfo += "Pre-Issue Buffer:\n"
        entry = self.mipsScoreBoarding.pre_issue.get(0, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 0:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.pre_issue.get(1, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 1:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.pre_issue.get(2, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 2:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.pre_issue.get(3, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 3:%s\n" % (("["+entry+"]") if entry != "" else (""))

        siminfo += "Pre-ALU Queue:\n"
        entry = self.mipsScoreBoarding.pre_alu.get(0, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 0:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.pre_alu.get(1, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 1:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.post_alu["inst"]
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "Post-ALU Buffer:%s\n" % (("["+entry+"]") if entry != "" else (""))

        siminfo += "Pre-ALUB Queue:\n"
        entry = self.mipsScoreBoarding.pre_alub.get(0, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 0:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.pre_alub.get(1, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 1:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.post_alub["inst"]
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "Post-ALUB Buffer:%s\n" % (("["+entry+"]") if entry != "" else (""))

        siminfo += "Pre-MEM Queue:\n"
        entry = self.mipsScoreBoarding.pre_mem.get(0, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 0:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.pre_mem.get(1, "")
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "\tEntry 1:%s\n" % (("["+entry+"]") if entry != "" else (""))
        entry = self.mipsScoreBoarding.post_mem["inst"]
        if entry != "":
            op = entry.replace(",", "").split(" ")
            opname = op[0] + "\t"
            entry = entry.replace(op[0] + " ", opname)
        siminfo += "Post-MEM Buffer:%s\n" % (("["+entry+"]") if entry != "" else (""))
        siminfo +="\n"

        siminfo +="Registers\n"
        siminfo += "R00:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n"\
               "R08:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n"\
                "R16:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" \
               "R24:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n\n" % tuple(self.__regFlie)
        siminfo += "Data"

        for i in range(self.__dataStart, self.__dataEnd, self.__instLen):
            if (i - self.__dataStart) % (self.__instLen * 8) == 0:
                siminfo += "\n"+`i` + ":\t%d" % self.__dataSegment.get(i)
            else:
                siminfo += "\t%d" % self.__dataSegment.get(i)

        siminfo += "\n"
        print siminfo
        self.__writeSim += siminfo

    def simulator(self):

        self.__pc = self.__codeStart
        cycles = 1
        exitflag = False
        while(True):
            #IF
            fetched_list = []
            #for i in range(0,2):
            #    fetched_inst = self.IF()
            #    if fetched_inst == "BREAK":
            #        exitflag = True
            #    if fetched_inst != "":
            #        fetched_list.append(fetched_inst)

            self.IF(fetched_list)
            #issue
            tmp_pre_mem = []
            tmp_pre_alu = []
            tmp_pre_alub = []
            self.Issue(tmp_pre_mem,tmp_pre_alu,tmp_pre_alub)

            # execution
            tmp_post_mem = {"result": "", "inst": ""}
            tmp_post_alu = {"result": "", "inst": ""}
            tmp_post_alub = {"result": "", "inst": ""}
            self.Execution(tmp_post_alu,tmp_post_alub,tmp_post_mem)

            # Write result
            self.WriteResult()



            if exitflag == True:
                break
            # update pre issue buffer
            index = -1
            for key in self.mipsScoreBoarding.pre_issue:
                index = key
            index += 1
            for inst in fetched_list:
                self.mipsScoreBoarding.pre_issue.update({index: inst})
                index += 1

            #update pre pre mem/alu/alub
            index = -1
            for key in self.mipsScoreBoarding.pre_mem:
                index = key
            index += 1
            for inst in tmp_pre_mem:
                self.mipsScoreBoarding.pre_mem.update({index:inst})
                index +=1

            index = -1
            for key in self.mipsScoreBoarding.pre_alu:
                index = key
            index += 1
            for inst in tmp_pre_alu:
                self.mipsScoreBoarding.pre_alu.update({index: inst})
                index += 1

            index = -1
            for key in self.mipsScoreBoarding.pre_alub:
                index = key
            index += 1
            for inst in tmp_pre_alub:
                self.mipsScoreBoarding.pre_alub.update({index: inst})
                index += 1

            #update post buffer
            self.mipsScoreBoarding.post_mem["result"] = tmp_post_mem["result"]
            self.mipsScoreBoarding.post_mem["inst"] = tmp_post_mem["inst"]
            self.mipsScoreBoarding.post_alu["result"] = tmp_post_alu["result"]
            self.mipsScoreBoarding.post_alu["inst"] = tmp_post_alu["inst"]
            self.mipsScoreBoarding.post_alub["result"] = tmp_post_alub["result"]
            self.mipsScoreBoarding.post_alub["inst"] = tmp_post_alub["inst"]

            # print
            self.print_simInfo(cycles)
            if self.mipsScoreBoarding.if_statu["exec"] == "BREAK":
                break
            cycles += 1

        self.write_file(self.__writeSim,"simulation.txt")















    #def simulator(self):


if __name__ == '__main__':
    codeFile = "sample.txt"
    disassemblyFile = "disassembly.txt"
    simulationFile = "simulation.txt"
    #parser = argparse.ArgumentParser()
    #parser.add_argument('testfile', default='sample.txt', help='name of input test file')
    #parser.add_argument('--disassemble', '-d', default='disassembly.txt', help='name of output disassembled file')
    #parser.add_argument('--simulate', '-s', default='simulation.txt', help='name of output simulated file')
    #args = parser.parse_args()


    #mips = MIPS(args.testfile,args.disassemble, args.simulate)
    mips = MIPS(codeFile, disassemblyFile, simulationFile)
    mips.disassemble()
    mips.simulator()
