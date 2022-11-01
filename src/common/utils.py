#coding=utf8
def pretty_json(data, prefix = ""):
    def show(data, prefix= ""):
        s = ""
        for k in data:
            v = data[k]
            if isinstance(v, dict):
                s += "%s- %s:\n%s" %(prefix, k, show(v, prefix+"  "))
            else: 
                val = str(v).replace("\n", " ")
                if len(val) > 300:
                    val = val[:300] + "...(共%s字符)" %(len(val))
                s += "%s- %s: %s\n" %(prefix, k, val)
        return s
    data = show(data, prefix)
    return data