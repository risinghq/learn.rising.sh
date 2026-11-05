class Trabajo:
    def __init__(self, etiquetas):
        self.tags = list(etiquetas)

    def update_tags(self, etiquetas):
        self.tags = list(dict.fromkeys(etiquetas))
        return self.tags


def anadir_etiqueta(trabajo, etiqueta):
    return trabajo.update_tags([*trabajo.tags, etiqueta])
