class Context:
    def __init__(self, id):
        self.id = id         # 全局唯一标识
        self.read_only = {}
        return 
    def __parse_flag_key(self, flag_key):
        return flag_key.split(".")
    
    def set(self, flag_key, value):
        keys = self.__parse_flag_key(flag_key)
        print(keys)
        keys_len = len(keys)
        read_only = self.read_only

        for i in range(keys_len):
            if not isinstance(read_only, dict):
                return False
            if i == keys_len - 1: 
                read_only[keys[i]] = value
            else:
                if keys[i] not in read_only:
                    read_only[keys[i]] = {}
                read_only = read_only[keys[i]]
        return True


    def get(self, flag_key, default_value = None):
        keys = self.__parse_flag_key(flag_key)
        data = self.read_only
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default_value
        return data

if __name__ == "__main__":
    ctx = Context(9999)
    ctx.set("cjf.name", "cjf")
    ctx.set("cjf.age", "26")
    ctx.set("cjf.wife", {"name" : "cjj", "age" : 99})
    print(ctx.read_only)
    print(ctx.get("cjf.wife.name"))