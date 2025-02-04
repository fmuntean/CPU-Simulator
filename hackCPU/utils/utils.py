import os
import string


def getVMFiles(folder:string):
    return getFiles(folder,'.vm')

def getJackFiles(folder:string):
   return getFiles(folder,'.jack')

def getFiles(folder:string, extension:string):
  ret =[]
  # r=root, d=directories, f = files
  for r, d, f in os.walk(folder):
    for file in f:
      if file.endswith(extension):
          ret.append(os.path.join(r, file))
  return ret
 