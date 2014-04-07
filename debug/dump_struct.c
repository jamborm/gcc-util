/* Helper function for dump_struct, dumps a substructure type TYPE, indented by
   INDENT.  */

static void
dump_struct_1 (FILE *f, tree type, int indent)
{
  tree fld;
  static char buffer[100];

  print_node_brief (f, "type:", type, 1);

  switch (TREE_CODE (type))
    {
    case RECORD_TYPE:
    case UNION_TYPE:
    case QUAL_UNION_TYPE:
      fprintf (f, " size in bytes: %i\n",
               (int) int_size_in_bytes (type));
      for (fld = TYPE_FIELDS (type); fld; fld = TREE_CHAIN (fld))
        {
          int i;
          if (TREE_CODE (fld) != FIELD_DECL)
            continue;

          for (i = 0; i < indent; i++)
            putc(' ', f);

          snprintf (buffer, 100, "offset: %u",
                    (unsigned) int_bit_position (fld));
          print_node_brief (f, buffer, fld, indent);
          dump_struct_1 (f, TREE_TYPE (fld), indent + 2);
        }

      break;
    case ARRAY_TYPE:
      print_node_brief (f, "element: ", TREE_TYPE (type), 1);

      /* fall through */
    default:
      fprintf (f, "\n");
      break;
    }
  return;
}

/* Dump the type of tree T to F in a way that makes it easy to find out
   which offsets correspond to what fields/elements.  Indent by INDENT.  */

static void
dump_struct (FILE *f, tree t, int indent)
{
  tree type;

  if (TYPE_P (t))
    type = t;
  else
    type = TREE_TYPE (t);

  print_generic_expr (f, t, 0);
  print_node_brief (f, " - ", t, indent);

  if (POINTER_TYPE_P (type))
    {
      fprintf (f, " -> ");
      dump_struct_1 (f, TREE_TYPE (type), indent + 2);
    }
  else
    dump_struct_1 (f, type, indent);
}
