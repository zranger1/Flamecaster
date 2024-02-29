from remi.gui import *


class SingleRowSelectionTable(TableWidget):
    """ An "improved" TableWidget that allows single
        row selection and highlighting.
    """

    def __init__(self, *arg, **kwargs):
        super(SingleRowSelectionTable, self).__init__(*arg, **kwargs)
        self.last_clicked_row = None
        self.last_item_clicked = None

        # keep a per-row dictionary of TableRow objects and associated configDatabase keys
        self.row_keys = {}

    def clear_row_keys(self):
        """Clear the row_keys dictionary."""
        self.row_keys = {}

    def set_row_key(self, row: int, key):
        """Set the row object's index(key) in the table.

        Args:
            row (int): a row number
            key (str): the key to set
        """
        # get the row's TableRow object from the table
        rowObject = self.children[str(row)]
        self.row_keys[rowObject] = key

    def get_row_key(self, row):
        """Returns the row object's associated database index string in the table.
           Returns None in case of item not found.

        Args:
            row (int): a TableRow object
        """
        return self.row_keys.get(row, None)

    @decorate_event
    def on_table_row_click(self, row, item):
        """ Highlight selected row, return the row and item clicked."""
        if self.last_clicked_row is not None:
            del self.last_clicked_row.style['outline']

        # only react to clicks on valid data rows
        # get the last key in self.children - we leave this row blank to keep
        # the table from stretching the last row to a silly height.
        last_key = list(self.children.keys())[-1]

        if row != self.children['0'] and row != self.children[last_key]:
            self.last_clicked_row = row
            self.last_item_clicked = item
            self.last_clicked_row.style['outline'] = "2px dotted blue"

        else:
            self.last_clicked_row = None
            self.last_item_clicked = None

        return row, item
