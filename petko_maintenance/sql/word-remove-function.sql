-- Petko HA: deactivate words from old "remove" reports (no pg_cron needed).
-- Called hourly by petko_maintenance add-on.

create or replace function public.process_old_remove_word_reports()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  processed_count integer := 0;
begin
  with remove_reports as (
    select distinct lower(btrim(word)) as normalized_word
    from public.word_reports
    where action = 'remove'
      and btrim(word) <> ''
      and (created_at at time zone 'Europe/Belgrade')::date
        < (now() at time zone 'Europe/Belgrade')::date
  ),
  updated_words as (
    update public.words w
    set active = false,
        updated_at = now(),
        note = concat_ws(
          ' | ',
          nullif(w.note, ''),
          'Auto removed from word_reports'
        )
    from remove_reports r
    where lower(btrim(w.word)) = r.normalized_word
    returning w.word
  ),
  deleted_reports as (
    delete from public.word_reports wr
    where wr.action = 'remove'
      and (wr.created_at at time zone 'Europe/Belgrade')::date
        < (now() at time zone 'Europe/Belgrade')::date
    returning wr.id
  )
  select count(*) into processed_count
  from deleted_reports;

  return processed_count;
end;
$$;
