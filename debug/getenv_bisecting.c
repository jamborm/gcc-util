stuff foo (void)
{

  bool print = false;
  static int counter = 0;
  const char *sl = getenv ("BS_LOW");
  counter ++;

  if (sl)
    {
      const char *sh = getenv ("BS_HIGH");
      int h,l = atoi (sl);
      gcc_assert (sh);

      h = atoi (sh);
      if (counter == l || counter == h)
        print = true;
      else if (counter > l && counter < h)
        return the_old_method ();
    }

  the_new_method ();

  if (print)
    {
      fprintf (stderr, "In function ");
      debug_generic_expr (current_function_decl);
      fprintf (stderr, "processed by the new method.");
    }

  return new_stuff;
}
