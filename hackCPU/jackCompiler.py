

import os
import string

from utils import JackAnalyzer



def getJackFiles(srcFolder:string):
  ret =[]
   # r=root, d=directories, f = files
  for r, d, f in os.walk(srcFolder):
    for file in f:
      if file.endswith(".jack"):
          ret.append(os.path.join(r, file))
  return ret


if __name__ == '__main__':
  srcFolder = 'Lab10/ArrayTest' #argv[1]
  srcFolder = 'lab10/ExpressionLessSquare'
  srcFolder = 'lab10/Square'
  srcFolder = 'lab11/Seven'
  #srcFolder = 'lab11/ConvertToBin'
  #srcFolder = 'lab11/Average'
  #srcFolder = 'lab11/ComplexArrays'
  srcFolder = 'lab11/Pong'
  #srcFolder = 'lab11/Square'
  srcFolder = 'lab12/ArrayTest'
  srcFolder = 'lab12/KeyboardTest'
  srcFolder = 'lab12/MathTest'
  srcFolder = 'lab12/MemoryTest'
  srcFolder = 'lab12/outputTest'
  srcFolder = 'lab12/ScreenTest'
  srcFolder = 'lab12/StringTest'
  

  includeFiles = ['lab12/String.jack','lab12/Output.jack','lab12/Memory.jack','lab12/Sys.jack'] #,'lab12/Screen.jack','lab12/Math.jack'] ,'Lab12/Array.jack','lab12/Keyboard.jack']


  if srcFolder.endswith('.jack'):
    srcFile = srcFolder
    print(f"\n Processing file: {srcFile}\n")
    #tknzr = JackTokenizer(srcFile)
    with open(srcFile[:-4]+'vm',mode='w') as vmFile:
      anlzr = JackAnalyzer(srcFile,vmFile)
      tokens =  anlzr.execute()

  for srcFile in getJackFiles(srcFolder) + includeFiles:
    print(f"\n Processing file: {srcFile}\n")
    #tknzr = JackTokenizer(srcFile)
    vmFile = srcFolder+'/'+srcFile.split('/')[-1][:-4]+'vm'  if srcFile in includeFiles else srcFile[:-4]+'vm'
    with open(vmFile,mode='w') as vmFile:
      anlzr = JackAnalyzer(srcFile,vmFile)
      tokens = anlzr.execute()
    
    

  
    
    
    