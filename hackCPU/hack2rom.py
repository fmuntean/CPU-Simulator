

from sys import argv


def help():
  print()
  print("HACK2ROM:")
  print("usage: ./hack2rom <hackFile>")
  print('generates a rom file from the hack file')
  pass

if __name__ == '__main__':
  #hackFile = "hackCPU/pong/pong.hack" # argv[1]
  if len(argv)==1:
    help()
  else:
    hackFile = argv[1]
    romFile = hackFile.replace('.hack','.rom') 
    with open(hackFile,mode="r") as hack:
      with open(romFile,mode="w") as rom:
        for line in hack:
          rom.write(f"0x{int(line, 2):04X}\n")