class TextHistory:
    def __init__(self):
        self._text = ""
        self._version = 0
        self._actions = {}

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value: str):
        raise AttributeError

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value: int):
        raise AttributeError

    def action(self, action: "Action") -> int:
        if isinstance(action, InsertAction):
            return self.insert(
                text=action.text,
                pos=action.pos,
                from_version=action.from_version,
                to_version=action.to_version,
            )
        elif isinstance(action, ReplaceAction):
            return self.replace(
                text=action.text,
                pos=action.pos,
                from_version=action.from_version,
                to_version=action.to_version,
            )
        elif isinstance(action, DeleteAction):
            return self.delete(
                pos=action.pos,
                length=action.length,
                from_version=action.from_version,
                to_version=action.to_version,
            )
        return self.version

    def insert(self, text: str, pos=None, from_version=None, to_version=None) -> int:
        if pos == -1:
            raise ValueError

        if pos is None:
            pos = len(self.text)

        if from_version is not None and from_version != self.version:
            raise ValueError
        else:
            from_version = self.version

        if pos > len(self.text):
            raise ValueError

        self._text = self.text[:pos] + text + self.text[pos:] if pos != len(self.text) else self.text + text

        self._version = to_version if to_version else self.version + 1

        self._actions[from_version] = InsertAction(
            text=text, pos=pos, from_version=from_version, to_version=self.version
        )
        return self.version

    def replace(self, text: str, pos=None, from_version=None, to_version=None) -> int:
        if pos == -1:
            raise ValueError

        if pos is None:
            pos = len(self.text)

        if from_version is not None and from_version != self.version:
            raise ValueError
        else:
            from_version = self.version

        if pos > len(self.text):
            raise ValueError

        self._text = (
            self.text[:pos] + text + self.text[pos + len(text) :] if pos != len(self.text) else self.text + text
        )

        self._version = to_version if to_version else self.version + 1

        self._actions[from_version] = ReplaceAction(
            text=text, pos=pos, from_version=from_version, to_version=self.version
        )
        return self.version

    def delete(self, pos: int, length: int, from_version=None, to_version=None) -> int:
        if pos == -1:
            raise ValueError

        if pos is None:
            pos = -1

        if from_version is not None and from_version != self.version:
            raise ValueError
        else:
            from_version = self.version

        if pos + length > len(self.text):
            raise ValueError

        self._text = self.text[:pos] + self.text[pos + length :]

        self._version = to_version if to_version else self.version + 1

        self._actions[from_version] = DeleteAction(
            pos=pos, length=length, from_version=from_version, to_version=self.version
        )
        return self.version

    def get_actions(self, from_version: int = 0, to_version: int = 0):
        if from_version < 0:
            raise ValueError("from_version must be >= 0")
        
        if to_version > self.version:
            raise ValueError("to_version must be <= current version")

        if from_version == to_version:
            return []
        
        if to_version == 0:
            to_version = self.version

        if to_version < from_version:
            raise ValueError("to_version must be > from_version")

        

        res = []

        for key in self._actions.keys():
            action = self._actions[key]
            if not (from_version <= key <= to_version):
                continue

            if not res:
                res.append(action)
                continue

            last_action = res[-1]

            if type(last_action) is type(action):
                res[-1] = self._merge_actions(last_action, action)
            else:
                res.append(action)

        return res

    def _merge_actions(self, a, b):
        action_to_append_data = {
            "pos": min(a.pos, b.pos),
            "from_version": min(a.from_version, b.from_version),
            "to_version": max(a.to_version, b.to_version),
        }
        if type(b) in (InsertAction, ReplaceAction):
            action_to_append_data["text"] = a.text + b.text
        elif type(b) is DeleteAction:
            action_to_append_data["length"] = a.length + b.length
        return type(a)(**action_to_append_data)


class Action:
    pass


class InsertAction(Action):
    def __init__(self, pos, text, from_version, to_version):
        self.pos = pos
        self.text = text
        self.from_version = from_version
        self.to_version = to_version

    def __repr__(self):
        return f"InsertAction obj: {self.pos=}, {self.text=}, {self.from_version=},  {self.to_version=}"


class ReplaceAction(Action):
    def __init__(self, pos, text, from_version, to_version):
        self.pos = pos
        self.text = text
        self.from_version = from_version
        self.to_version = to_version

    def __repr__(self):
        return f"ReplaceAction obj: {self.pos=}, {self.text=}, {self.from_version=},  {self.to_version=}"


class DeleteAction(Action):
    def __init__(self, pos, length, from_version, to_version):
        self.pos = pos
        self.length = length
        self.from_version = from_version
        self.to_version = to_version

    def __repr__(self):
        return f"DeleteAction obj: {self.pos=}, {self.length=}, {self.from_version=},  {self.to_version=}"
