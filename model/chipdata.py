                   
                                                         
                                                     

class ChipData:


    def __init__(self, pos: str, name: str, value: str, desc: str = ""):
        self.pos = pos                        
        self.name = name                              
        self.value = value                 
        self.desc = desc                           

    def to_dict(self):
        return {
            "pos": self.pos,
            "name": self.name,
            "value": self.value,
            "desc": self.desc
        }

    @staticmethod
    def from_dict(d):
        return ChipData(d["pos"], d["name"], d["value"], d.get("desc", ""))

    def __str__(self):
        return f"{self.pos}: {self.name} = {self.value} ({self.desc})"
