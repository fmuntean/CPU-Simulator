class Parser:
  def Parse(self,line):
    ret = line.strip().split(' ')
    while len(ret)<3:
      ret.append(None)
    return (ret)