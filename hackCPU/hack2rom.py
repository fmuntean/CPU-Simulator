



if __name__ == '__main__':
  hackFile = "hackCPU/pong/pong.hack" # argv[1]
  romFile = hackFile+'.rom' 
  with open(hackFile,mode="r") as hack:
    with open(romFile,mode="w") as rom:
      for line in hack:
        rom.write(f"0x{int(line, 2):04X}\n")