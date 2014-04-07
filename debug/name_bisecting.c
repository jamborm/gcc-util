static bool
process_this_file (void)
{
  static bool decided = false;
  static bool process;

  if (!decided)
    {
      const char *bisect_mode = getenv ("NAME_BISECT_MODE");
      const char *namelog = getenv ("NAME_BISECT_NAMELOG");

      decided = true;
      if (!bisect_mode)
	{
	  process = true;
	  return process;
	}

      if (strcmp(bisect_mode , "GEN_ALL") == 0)
	{
	  FILE *f;
	  gcc_assert (namelog);

          f = fopen (namelog, "a");
          gcc_assert (f);
          fprintf (f, "%s\n", main_input_filename);
          fclose (f);

	  process = true;
	  return process;
	}
      else if (strcmp(bisect_mode , "BISECT") == 0)
	{
	  const char *low = getenv ("NAME_BISECT_LOW");
	  const char *high = getenv ("NAME_BISECT_HIGH");

	  gcc_assert (low && high);

	  if ((strcmp (low, main_input_filename) <= 0)
	      && (strcmp (main_input_filename, high) <= 0))
	    {
	      if (namelog)
		{
		  FILE *f = fopen (namelog, "a");
		  gcc_assert (f);
		  fprintf (f, "Processing %s\n", main_input_filename);
		  fclose (f);
		}
	      process = true;
	      return process;
	    }
	  else
	    {
	      process = false;
	      return process;
	    }
        }
      else
        process = true;
    }
  return process;
}
