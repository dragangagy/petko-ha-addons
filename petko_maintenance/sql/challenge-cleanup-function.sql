-- Petko SR: challenge card cleanup (optional; needs record_witch_hunt_result on petko_sr).

create or replace function public.cleanup_old_challenges()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  deleted_count integer := 0;
  step_count integer := 0;
  belgrade_today date := (now() at time zone 'Europe/Belgrade')::date;
  dow integer := extract(isodow from belgrade_today)::integer;
  weekend_start date := belgrade_today - ((dow + 1) % 7);
begin
  if to_regprocedure('public.record_witch_hunt_result(date)') is not null then
    begin
      perform public.record_witch_hunt_result(weekend_start);
    exception when others then
      null;
    end;
  end if;

  delete from public.challenges
  where status = 'pending'
    and opponent_device is null
    and accepted_at is null
    and created_at < now() - interval '6 hours'
    and not (
      extract(isodow from (created_at at time zone 'Europe/Belgrade')) in (6, 7)
      and now() < (
        date_trunc('week', created_at at time zone 'Europe/Belgrade')
        + interval '7 days'
      ) at time zone 'Europe/Belgrade'
    );
  get diagnostics step_count = row_count;
  deleted_count := deleted_count + step_count;

  delete from public.challenges
  where status = 'accepted'
    and coalesce(accepted_at, created_at) < now() - interval '24 hours'
    and not (
      extract(isodow from (created_at at time zone 'Europe/Belgrade')) in (6, 7)
      and now() < (
        date_trunc('week', created_at at time zone 'Europe/Belgrade')
        + interval '7 days'
      ) at time zone 'Europe/Belgrade'
    );
  get diagnostics step_count = row_count;
  deleted_count := deleted_count + step_count;

  delete from public.challenges
  where status = 'played'
    and (
      case
        when extract(isodow from (created_at at time zone 'Europe/Belgrade')) in (6, 7)
          then now() >= (
            date_trunc('week', created_at at time zone 'Europe/Belgrade')
            + interval '12 days'
          ) at time zone 'Europe/Belgrade'
        else greatest(
          coalesce(creator_played_at, created_at),
          coalesce(opponent_played_at, created_at),
          coalesce(accepted_at, created_at),
          created_at
        ) < now() - interval '24 hours'
      end
    );
  get diagnostics step_count = row_count;
  deleted_count := deleted_count + step_count;

  delete from public.challenges
  where status = 'cancelled'
    and created_at < now() - interval '1 hour';
  get diagnostics step_count = row_count;
  deleted_count := deleted_count + step_count;

  return deleted_count;
end;
$$;
