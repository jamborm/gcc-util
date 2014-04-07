static void
append_to_tmp_log (const char *str)
{
  FILE *f = fopen ("/tmp/ira_sw_prep", "a");
  gcc_assert(f);
  fprintf (f, "%s %u %u: %s\n", main_input_filename,
	   (unsigned) getpid(), DECL_UID (current_function_decl), str);
  fclose (f);
  return;
}
