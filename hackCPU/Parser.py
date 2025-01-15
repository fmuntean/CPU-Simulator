import re


class Parser:
  def Parse(self,line):
    #cmt = line.find("//")
    #if cmt>0:
    #  line=line[0..cmt]
    ret = re.split(' |\t|\n|//', line.strip())
    while len(ret)<3:
      ret.append(None)
    return (ret[:3])