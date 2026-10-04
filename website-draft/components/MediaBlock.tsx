import Image from "next/image";
import type { Media } from "@/content/solutions";
export function ResponsiveImage({
  media,
  priority = false,
}: {
  media: Media;
  priority?: boolean;
}) {
  return (
    <Image
      src={media.src}
      alt={media.alt}
      width={1237}
      height={720}
      sizes="(max-width: 800px) 100vw, 50vw"
      priority={priority}
      className="responsive-image"
    />
  );
}
export function ResponsiveVideo({ media }: { media: Media }) {
  return (
    <video
      controls
      playsInline
      preload="none"
      poster={media.poster}
      aria-label={media.alt}
    >
      <source src={media.src} />
      <a href={media.src}>{media.alt}</a>
    </video>
  );
}
export function MediaBlock({
  media,
  priority = false,
}: {
  media: Media;
  priority?: boolean;
}) {
  return (
    <figure className="media-block">
      {media.type === "video" ? (
        <ResponsiveVideo media={media} />
      ) : (
        <ResponsiveImage media={media} priority={priority} />
      )}
      {media.caption && <figcaption>{media.caption}</figcaption>}
    </figure>
  );
}
