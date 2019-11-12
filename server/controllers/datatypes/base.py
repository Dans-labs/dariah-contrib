from config import Config as C, Names as N
from controllers.html import HtmlElements as H

from controllers.utils import pick as G, E


CW = C.web

QQ = H.icon(CW.unknown[N.generic])

WRONG_TYPE = CW.messages


class TypeBase:
    """The base class for functions on typed values.

    This class is meant to be extended by classes dealing with specific types.
    It will be extended by Text and Numeric type classes, who in turn will be extended
    by concrete type classes. And there are the classes Value and Master which
    will be exteded by type classes for each value table and type classes for
    each master table respectively.

    See the config file tables.yaml, under keys `scalarTypes` and `boolTypes`.

    Attributes
    ----------
    widgetType: string
        The type of widget that this type needs to edit its value. E.g. `text`.
    rawType: type
        The Python type that is used to represent values of this type.
        If it is None, the rawType is not relevant.
    pattern: string(re)
        For text widgets, this is a regular expression that constrains what is legal
        input in the text input field.
    needsControl: boolean
        Whether methods of this type need to be supplied with the Control singleton.

    !!! note
        In order to compute the representation of a user, the Auth singleton inside the
        Control singleton is needed to detemine what parts of the user identifiaction
        the current user is allowed to see.
    """

    widgetType = None
    pattern = None
    rawType = None
    needsControl = False

    @staticmethod
    def validationMsg(tp):
        """A validation error message for a specific type.

        Parameters
        ----------
        tp: string
            The name under which a type is registered.

        Returns
        -------
        string
            An error message.  See web.yaml under key `wrongType`.
        """

        return G(WRONG_TYPE, tp)

    def normalize(self, strVal):
        """Normalizes a string representation of a value.

        Parameters
        ----------
        strVal: string
            The string rep that must be normalized.

        Returns
        -------
        string
            A normalized equivalent representation of the same value.
        """

        return str(strVal).strip()

    def fromStr(self, editVal):
        """Turns the output from an edit widget into a real value that can be saved.

        Parameters
        ----------
        editVal: string
            The output of an edit widget.

        Returns
        -------
        mixed
            A value of the type in question, corresponding to `editVal`.
        """

        if not editVal:
            return None
        val = self.normalize(editVal)
        cast = self.rawType
        return val if cast is None else cast(val)

    def toDisplay(self, val):
        """Turns a real value into a HTML code for readonly display.

        Parameters
        ----------
        val: mixed
            A value of this type.

        Returns
        -------
        string(html)
            Possibly with nice formatting depending on the nature of the value.
        """

        return QQ if val is None else H.span(H.he(self.normalize(str(val))))

    def toEdit(self, val):
        """Turns a real value into a string for editable display.

        Parameters
        ----------
        val: mixed
            A value of this type.

        Returns
        -------
        string
        """

        return E if val is None else self.normalize(str(val))

    def toOrig(self, val):
        """Turns a real value into an (original) value.

        The resulting value can be used for comparison with newly entered values
        in an edit widget at the client side.

        Parameters
        ----------
        val: mixed
            A value of this type.

        Returns
        -------
        boolean | string | None
        """

        if val is None:
            return None
        return str(val)

    def widget(self, val):
        """Constructs and edit widget around for this type.

        Parameters
        ----------
        val: string
            The initial value for the widget.

        Returns
        -------
        string(html)
            Dependent on a batch of Javascript in `index.js`, look for `const widgets`.
        """

        atts = {}
        if self.pattern:
            atts[N.pattern] = self.pattern
        validationMsg = TypeBase.validationMsg(self.name)

        widgetElem = H.input(self.toEdit(val), type=N.text, cls="wvalue", **atts)
        validationElem = H.span(E, valmsg=validationMsg) if validationMsg else E
        return H.join([widgetElem, validationElem])
