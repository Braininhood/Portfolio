-- Replace old Supabase project storage URLs with new project URLs
-- Old: https://tpwjhrurjiqefojvmrlj.supabase.co
-- New: https://zdairdvgiifsymgmoswf.supabase.co
-- Run this once after migrating to the new Supabase project.

DO $$
DECLARE
  old_host TEXT := 'https://tpwjhrurjiqefojvmrlj.supabase.co';
  new_host TEXT := 'https://zdairdvgiifsymgmoswf.supabase.co';
BEGIN
  -- profiles.avatar_url
  UPDATE public.profiles
  SET avatar_url = REPLACE(avatar_url, old_host, new_host)
  WHERE avatar_url IS NOT NULL AND avatar_url LIKE '%' || old_host || '%';

  -- mentor_profiles.image_url
  UPDATE public.mentor_profiles
  SET image_url = REPLACE(image_url, old_host, new_host)
  WHERE image_url IS NOT NULL AND image_url LIKE '%' || old_host || '%';

  -- mentor_reviews.user_avatar
  UPDATE public.mentor_reviews
  SET user_avatar = REPLACE(user_avatar, old_host, new_host)
  WHERE user_avatar IS NOT NULL AND user_avatar LIKE '%' || old_host || '%';

  -- mentor_courses.thumbnail_url
  UPDATE public.mentor_courses
  SET thumbnail_url = REPLACE(thumbnail_url, old_host, new_host)
  WHERE thumbnail_url IS NOT NULL AND thumbnail_url LIKE '%' || old_host || '%';

  -- mentor_products.file_url
  UPDATE public.mentor_products
  SET file_url = REPLACE(file_url, old_host, new_host)
  WHERE file_url IS NOT NULL AND file_url LIKE '%' || old_host || '%';

  -- mentor_products.preview_image_url
  UPDATE public.mentor_products
  SET preview_image_url = REPLACE(preview_image_url, old_host, new_host)
  WHERE preview_image_url IS NOT NULL AND preview_image_url LIKE '%' || old_host || '%';

  -- mentor_video_answers.video_url
  UPDATE public.mentor_video_answers
  SET video_url = REPLACE(video_url, old_host, new_host)
  WHERE video_url IS NOT NULL AND video_url LIKE '%' || old_host || '%';

  -- mentor_avatars.photo_urls (TEXT[])
  UPDATE public.mentor_avatars
  SET photo_urls = (
    SELECT array_agg(REPLACE(u, old_host, new_host) ORDER BY ord)
    FROM unnest(photo_urls) WITH ORDINALITY AS t(u, ord)
  )
  WHERE photo_urls IS NOT NULL AND EXISTS (
    SELECT 1 FROM unnest(photo_urls) u WHERE u LIKE '%' || old_host || '%'
  );

  -- mentor_avatars.voice_sample_url
  UPDATE public.mentor_avatars
  SET voice_sample_url = REPLACE(voice_sample_url, old_host, new_host)
  WHERE voice_sample_url IS NOT NULL AND voice_sample_url LIKE '%' || old_host || '%';

  -- product_reviews.user_avatar
  UPDATE public.product_reviews
  SET user_avatar = REPLACE(user_avatar, old_host, new_host)
  WHERE user_avatar IS NOT NULL AND user_avatar LIKE '%' || old_host || '%';

  -- messages.file_url
  UPDATE public.messages
  SET file_url = REPLACE(file_url, old_host, new_host)
  WHERE file_url IS NOT NULL AND file_url LIKE '%' || old_host || '%';

  -- scheduled_messages.file_url
  UPDATE public.scheduled_messages
  SET file_url = REPLACE(file_url, old_host, new_host)
  WHERE file_url IS NOT NULL AND file_url LIKE '%' || old_host || '%';
END $$;
