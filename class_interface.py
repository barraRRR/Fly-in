class Interface:
    def __init__(self, map: str) -> None:
        self.map = MapParser(map)
        self.net = Network(**self.map.data)