import { motion, useTransform, type MotionValue } from 'motion/react';

/**
 * The title is a lightweight curved 3D letter surface, rather than a single
 * flat DOM plane. Its glyphs roll away from the centre onto a virtual cylinder.
 * Parent motion carries the curved text around the pillar as a ring segment.
 * The rear of the segment stays visible, as in the reference's true 3D ring.
 */
type CurvatureProps = {
  progress: MotionValue<number>;
  reducedMotion: boolean;
};

const brand = 'VerifAI';
const words = ['AI', 'hallucinates.', 'We', 'investigate.'];

function CurvedLetter({
  letter, index, total, progress, reducedMotion,
}: CurvatureProps & {letter: string; index: number; total: number}) {
  // Normalize the left and right sides around the cylinder's front.
  const side = (index - (total - 1) / 2) / ((total - 1) / 2);
  const distance = Math.abs(side);
  // Unroll the flat title into a cylindrical ring segment. Each glyph
  // occupies a tangent plane; edge glyphs recede rather than fan outward.
  const rotateY = useTransform(progress, [0, .12, .32, .60], [
    0, 0, -side * 76, -side * 115,
  ]);
  const x = useTransform(progress, [0, .12, .32, .60], [
    0, 0, -side * 23, -side * 51,
  ]);
  const z = useTransform(progress, [0, .12, .32, .60], [
    0, 0, -distance * distance * 105, -distance * distance * 250,
  ]);
  return (
    <motion.span
      className="va-metallic-letter"
      style={reducedMotion ? undefined : {rotateY, x, z}}
    >{letter}</motion.span>
  );
}

function CurvedWord({
  word, index, progress, reducedMotion,
}: CurvatureProps & {word: string; index: number}) {
  const side = (index - (words.length - 1) / 2) / ((words.length - 1) / 2);
  const rotateY = useTransform(progress, [0, .12, .32, .60], [
    0, 0, -side * 48, -side * 81,
  ]);
  const z = useTransform(progress, [0, .12, .32, .60], [
    0, 0, -side * side * 56, -side * side * 125,
  ]);
  return (
    <motion.span
      className="va-metallic-word"
      style={reducedMotion ? undefined : {rotateY, z}}
    >{word}</motion.span>
  );
}

export function MetallicHeroTitle({progress, reducedMotion}: CurvatureProps) {
  return (
    <>
      <h1 id="va-hero-title" aria-label={brand} className="va-metallic-title">
        <span className="va-metallic-letters" aria-hidden="true">
          {[...brand].map((letter,index) => (
            <CurvedLetter
              key={index}
              letter={letter}
              index={index}
              total={brand.length}
              progress={progress}
              reducedMotion={reducedMotion}
            />
          ))}
        </span>
      </h1>
      <p className="va-metallic-slogan" aria-label="AI hallucinates. We investigate.">
        <span className="va-metallic-slogan-line" aria-hidden="true">
          {words.map((word,index) => (
            <CurvedWord
              key={word}
              word={word}
              index={index}
              progress={progress}
              reducedMotion={reducedMotion}
            />
          ))}
        </span>
      </p>
    </>
  );
}

