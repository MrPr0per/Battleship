from interface.base_elements import Grid


class MyEvent:
    pass

class EventPickingUp(MyEvent):
    def __init__(self, picking_up_crd, ship:Grid):
        self.picking_up_crd = picking_up_crd
        self.ship = ship

