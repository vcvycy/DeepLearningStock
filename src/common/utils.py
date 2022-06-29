#coding=utf8
def pretty_json(data, prefix = ""):
    def show(data, prefix= ""):
        s = ""
        for k in data:
            v = data[k]
            if type(v) == type({}):
                s += "%s- %s:\n%s" %(prefix,k, show(v, prefix+"  "))
            else:
                s += "%s- %s: %s\n" %(prefix, k, str(v).replace("\n", " ")[:300])
        return s
    data = show(data, prefix)
    return data