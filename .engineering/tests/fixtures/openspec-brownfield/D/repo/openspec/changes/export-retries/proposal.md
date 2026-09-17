# Reliable exports

Add an export feature in two slices: serialize rows, then deliver them in the
background with retry after transient failure. Before this change there was no
export serializer. The serializer slice is now implemented; delivery remains.
