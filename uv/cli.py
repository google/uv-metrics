"""CLI utilities."""


def list_of(type=str, separator=' '):
  """Returns a function that you can pass to `argparse.add_argument`'s `type`
  keyword. This type will accept either:

  - items of type `type`, or
  - a string containing multiple items of type `type`, separated by `separator`."""

  def f(s):
    try:
      return type(s)
    except ValueError:
      return [f(i) for i in s.split(separator)]

  return f


class FlatList(list):
  """List that, on append, appends non-lists, or if you try to append a list,
  appends all items INSIDE that list instead of appending the list directly.

  """

  def append(self, arg):

    if isinstance(arg, list):
      [self.append(x) for x in arg]
    else:
      super(FlatList, self).append(arg)
