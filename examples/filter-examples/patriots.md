# Custom Filter

This page demonstrates custom filters in Dactyl. In "Metal Gear Solid 2", the Patriots are an organization who brainwash people to say "la-li-lu-le-lo" instead of "Patriots" when speaking aloud, even among their compatriots.

This page should read normally in the markdown source, but in the Dactyl output if the `patriots` filter is enabled, all instances of the Patriots' name is replaced with la-li-lu-le-lo.

If a custom filter name is satisfied by multiple custom filter directories, or by a custom filter and by a Dactyl built-in filter, the first listed custom filter directory takes highest preference, and the Dactyl built-in filters are lowest preference. However, if importing a filter fails (for example, due to a syntax error), a lower-precedence filter with the same name may be loaded instead.
