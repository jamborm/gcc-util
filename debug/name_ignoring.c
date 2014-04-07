static bool process_this_file (void)
{
  static bool decided = false;
  static bool ignore = false;

  if (!decided)
    {
      FILE *f;
      /*const char *p, *n = main_input_filename;
        bool plus = false;*/

      decided = true;
      if (strstr (main_input_filename, "tree-ssa-ccp.c"))
        {
          f = fopen ("/tmp/jamborm-namelog", "a");
          gcc_assert (f);
          fprintf (f, "%s (%i)\n", main_input_filename,
		   (int) MAY_HAVE_DEBUG_STMTS);

          fclose (f);
          ignore = true;
        }
      else
        ignore = false;
    }

  return !ignore;
}
