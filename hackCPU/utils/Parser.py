import re


class Parser:
  def Parse(self,line):
    ret = re.split(' |\t|\n|//', line.strip())
    while len(ret)<3:
      ret.append(None)
    return (ret[:3])