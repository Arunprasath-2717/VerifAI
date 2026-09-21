"""Exhaustive test matrix for claim extraction offset invariants and content classification."""

import pytest

from app.modules.claims.classifier import ContentClassifier
from app.modules.claims.extractor import DeterministicClaimExtractor
from app.schemas.verification import ContentType, VerdictType

classifier = ContentClassifier()
extractor = DeterministicClaimExtractor()

# 1. Diverse Factual Statements across scientific, geographic, and historical domains
FACTUAL_SAMPLES = [
    "The chemical formula for water is H2O.",
    "Mount Everest has an elevation of 8,848 meters above sea level.",
    "Albert Einstein published his paper on special relativity in 1905.",
    "The speed of light in a vacuum is approximately 299,792,458 meters per second.",
    "Jupiter is the largest planet in our solar system.",
    "The human heart typically beats between 60 and 100 times per minute at rest.",
    "Photosynthesis converts carbon dioxide and water into glucose and oxygen.",
    "The Declaration of Independence was adopted in 1776.",
    "DNA is composed of adenine, thymine, cytosine, and guanine.",
    "The Pacific Ocean is the largest and deepest of Earth's oceanic divisions.",
    "Helium is the second most abundant element in the observable universe.",
    "The Eiffel Tower was completed in 1889 for the Exposition Universelle.",
    "The boiling point of water at standard atmospheric pressure is 100 degrees Celsius.",
    "The Great Barrier Reef is located off the coast of Queensland, Australia.",
    "Mars has two small natural satellites named Phobos and Deimos.",
    "The Apollo 11 mission landed humans on the Moon in July 1969.",
    "Light takes approximately 8 minutes and 20 seconds to travel from the Sun to Earth.",
    "Nitrogen makes up roughly 78 percent of Earth's atmosphere.",
    "The Amazon River is the largest river by discharge volume of water in the world.",
    "Table salt is composed of sodium and chlorine ions forming sodium chloride.",
    "Isaac Newton published Philosophiæ Naturalis Principia Mathematica in 1687.",
    "The human body consists of approximately 60 percent water.",
    "Saturn's rings are predominantly composed of water ice particles and rocky debris.",
    "The periodic table currently contains 118 confirmed chemical elements.",
    "Tokyo is the capital city of Japan.",
    "The Tyrannosaurus rex lived during the late Cretaceous period.",
    "Sound travels through dry air at 20 degrees Celsius at roughly 343 meters per second.",
    "The Roman Empire reached its maximum territorial extent under Emperor Trajan in 117 AD.",
    "Diamond is an allotrope of carbon with a crystal lattice structure.",
    "The Sahara is the largest hot desert on Earth, spanning over 9 million square kilometers.",
    "Pluto was classified as a dwarf planet by the International Astronomical Union in 2006.",
    "The Magna Carta was originally issued by King John of England in 1215.",
    "A standard guitar typically has six strings tuned to E, A, D, G, B, and E.",
    "The diameter of the Earth at the equator is approximately 12,742 kilometers.",
    "Penicillin was discovered by Scottish physician Alexander Fleming in 1928.",
    "The Nile River flows northward through northeastern Africa into the Mediterranean Sea.",
    "The density of liquid water is approximately 1 gram per cubic centimeter.",
    "Oxygen is atomic number 8 on the periodic table of elements.",
    "Antarctica is Earth's southernmost and least populated continent.",
    "The Hubble Space Telescope was launched into low Earth orbit in 1990.",
    "Electrons carry a negative elementary electric charge.",
    "The Panama Canal connects the Atlantic Ocean with the Pacific Ocean.",
    "A regular hexagon has six equal sides and internal angles of 120 degrees.",
    "The human skeleton is composed of 206 bones in an adult.",
    "Silicon is a semiconductor widely utilized in integrated circuits and microchips.",
    "The treaty of Versailles ended the state of war between Germany and the Allied Powers.",
    "The moon orbits Earth at an average distance of approximately 384,400 kilometers.",
    "Gold is a transition metal with the atomic symbol Au and atomic number 79.",
    "The Dead Sea is a hypersaline lake located between Jordan, the West Bank, and Israel.",
    "A light-year is the distance that light travels in a vacuum in one Julian year.",
]

# 2. Subjective Opinions, Aesthetics, and Value Judgments
OPINION_SAMPLES = [
    "I believe that modern art lacks emotional depth.",
    "In my opinion, chocolate ice cream is far superior to vanilla.",
    "The cinematography in the film was absolutely breathtaking.",
    "I think remote work is much more productive than working in an office.",
    "Jazz is the most expressive and sophisticated musical genre ever created.",
    "The city's architectural design feels cold and uninspiring.",
    "I personally feel that autumn is the most pleasant season of the year.",
    "That restaurant offers the finest dining experience in the metropolitan area.",
    "Minimalist interior design creates a serene living environment.",
    "I feel that reading fiction develops empathy more effectively than non-fiction.",
    "The protagonist's decision in the final chapter seemed completely unjustified.",
    "In my viewpoint, electric vehicles have a much sleeker aesthetic.",
    "Classical music is inherently more calming than contemporary pop.",
    "I think handwritten letters possess a charm that digital messages cannot replicate.",
    "The author's prose is unnecessarily convoluted and pretentious.",
    "I believe sunrise is always more peaceful than sunset.",
    "In my view, vintage mechanical watches have more character than smartwatches.",
    "In our opinion, the museum exhibit was poorly curated and underwhelming.",
    "Traveling by train is undeniably the most relaxing way to see the countryside.",
    "I personally believe that learning a second language is the best cognitive exercise.",
    "The soundtrack elevated an otherwise mediocre narrative into something memorable.",
    "In my view, coffee tastes significantly better without sugar.",
    "The play's dialogue felt forced and unnatural.",
    "I think spending time in nature is the single most rejuvenating activity.",
    "In my opinion, film photography has a warmth and texture that digital sensors cannot match.",
    "I consider this novel to be the definitive masterpiece of the decade.",
    "In my opinion, simplicity is the ultimate sophistication in product design.",
    "The ambiance of the cafe is cozy and welcoming.",
    "I feel that silence is often more powerful than spoken words.",
    "Bicycle commuting is far more enjoyable than sitting in highway traffic.",
]

# 3. Future Predictions, Forecasts, and Speculations
PREDICTION_SAMPLES = [
    "Quantum computers will solve RSA encryption by the year 2035.",
    "Global temperatures are projected to increase by 1.5 degrees Celsius by 2040.",
    "Electric aviation will dominate regional commercial flights by 2050.",
    "Autonomous vehicles are expected to reduce urban traffic fatalities by 80 percent.",
    "Humanity will establish a permanent research base on Mars by 2045.",
    "Renewable energy is forecast to generate 90 percent of global electricity by 2050.",
    "Artificial general intelligence will be achieved within the next two decades.",
    "Sea levels will rise by up to one meter by the end of the century.",
    "Commercial space tourism will become accessible to middle-income families by 2060.",
    "The global population is projected to peak at nearly 10.3 billion during the 2080s.",
    "Fusion power plants will begin supplying commercial grid power in 2042.",
    "Microplastics will be completely phased out of consumer packaging by 2038.",
    "Urban vertical farming will provide half of all fresh produce by 2055.",
    "Smart contact lenses will replace smartphones as the primary computing display.",
    "High-speed hyperloop transit will connect major European capitals by 2048.",
    "Synthetic biology will eradicate malaria within the next thirty years.",
    "Global freshwater demand will exceed viable supply in several regions by 2035.",
    "Automated drone delivery networks will handle the majority of parcel logistics.",
    "Brain-computer interfaces will allow seamless telepathic communication by 2065.",
    "Lab-grown meat will achieve price parity with conventional agriculture by 2032.",
    "The Arctic Ocean will experience ice-free summers before the middle of the century.",
    "Wearable health monitors will detect cardiovascular diseases weeks before onset.",
    "Carbon capture technologies will achieve gigaton-scale removal by 2045.",
    "Quantum sensors will revolutionize underground navigation and mineral exploration.",
    "Decentralized power grids will make regional blackout cascades obsolete.",
]

# 4. Hypothetical Counterfactuals and Scenarios
HYPOTHETICAL_SAMPLES = [
    "What if the Library of Alexandria had never burned down?",
    "Suppose that gravity on Earth were suddenly reduced by half.",
    "Imagine a world where electricity had never been discovered.",
    "If dinosaurs had not gone extinct, mammalian evolution would have diverged completely.",
    "What if human beings possessed the ability to photosynthesize sunlight?",
    "Suppose that the speed of light were only 100 miles per hour.",
    "Imagine what society would look like if nobody required sleep.",
    "If the Roman Empire had developed steam engines, industrialization would have started early.",
    "What if oceans covered 95 percent of the planet's surface?",
    "Suppose that atmospheric oxygen concentration doubled overnight.",
    "Imagine a scenario where trees could communicate verbally with humans.",
    "If the Moon had two times its current mass, ocean tides would drown coastal cities.",
    "What if language had evolved entirely through visual gestures rather than sounds?",
    "Suppose that all fossil fuel deposits had never formed in Earth's crust.",
    "Imagine how geopolitics would change if clean energy became virtually free.",
    "If humans lived for an average of five hundred years, retirement models would collapse.",
    "What if teletransportation existed with zero latency between any two points on Earth?",
    "Suppose that Earth had two distinct suns orbiting in a binary star system.",
    "Imagine a planet where seasons lasted for an entire century.",
    "If the Earth's magnetic field collapsed completely, cosmic radiation would strip the ozone layer.",
]

# 5. Creative Fiction, Storytelling, and Metaphors
CREATIVE_SAMPLES = [
    "Once upon a time in a distant kingdom shrouded by silver mist.",
    "The emerald dragon unfurled its translucent wings above the frozen crags.",
    "The wizard cast a spell of azure flame upon the ancient parchment.",
    "A white unicorn grazed peacefully beside the enchanted spring.",
    "She waved her magic wand to transform the pumpkin into a crystal carriage.",
    "This fictional story recounts the voyages of the starlight voyager.",
    "The fairytale describes a hidden realm where trees sing ancient lullabies.",
    "Legend tells of a mythical guardian slumbering beneath the volcano.",
    "In a galaxy far away, starfighters defended the outer rim colonies.",
    "The grand wizard brewed a potion of liquid moonlight and crushed pearls.",
    "Once upon a time, two brothers ventured into the whispering forest.",
    "A fearsome dragon guarded the golden hoard within the mountain cavern.",
    "The unicorn touched its horn to the poisoned water to purify the river.",
    "He wielded the magic wand with supreme confidence during the duel.",
    "The fictional protagonist traversed dimensions through a rift in spacetime.",
    "Every fairytale reminds us that courage can overcome the darkest shadows.",
    "Legend tells of an invincible sword buried beneath the ocean floor.",
    "In a galaxy far away, astronomers discovered a planet of crystalline towers.",
    "The dragon soared across the crimson twilight sky towards its aerie.",
    "The wise wizard deciphered the runes etched into the standing stones.",
]

# 6. Natural Language Instructions and How-To Directives
INSTRUCTION_SAMPLES = [
    "Write a Python function to compute the Fibonacci sequence using memoization.",
    "Explain how to configure an async PostgreSQL connection pool with SQLAlchemy.",
    "List five key differences between relational databases and NoSQL document stores.",
    "Summarize the main arguments presented in the provided research paper.",
    "Create a responsive navigation bar using HTML and modern CSS flexbox.",
    "Describe the step-by-step process of cellular respiration in human mitochondria.",
    "Tell me how to bake sourdough bread from scratch with a wild yeast starter.",
    "Generate a secure bash script to back up MySQL databases to encrypted storage.",
    "Show me an example of binary search tree implementation in TypeScript.",
    "Help me troubleshoot a memory leak occurring in a Node.js microservice.",
    "Convert this JSON payload into a CSV format compatible with spreadsheet applications.",
    "Calculate the compound interest on a principal of ten thousand dollars over five years.",
    "Translate the following paragraph from English into Spanish maintaining formal register.",
    "Provide a detailed checklist for deploying a production web application to Kubernetes.",
    "Format this unstructured text into a clean Markdown table with headers.",
    "Design a scalable microservices architecture for an e-commerce checkout pipeline.",
    "Implement an LRU cache data structure with O(1) get and put operations.",
    "Review this pull request and identify potential SQL injection vulnerabilities.",
    "How do I reset my forgotten root password on an Ubuntu Linux server?",
    "How can I optimize slow database queries using appropriate indexes?",
    "How to configure HTTPS certificates using Let's Encrypt and Certbot?",
    "How do I set up a virtual environment in Python 3 on Linux?",
    "How can I profile CPU utilization in a multi-threaded Python application?",
    "How to serialize complex Pydantic models with custom JSON encoders?",
    "How do I configure CORS middleware in a FastAPI web service?",
]


class TestClaimTaxonomyMatrix:
    """Rigorous parameterization testing claim classification taxonomy and invariants."""

    @pytest.mark.parametrize("text", FACTUAL_SAMPLES)
    def test_factual_samples_classified_as_factual(self, text: str) -> None:
        """Verify empirical factual propositions are categorized as FACTUAL."""
        result = classifier.classify(text)
        assert result.content_type == ContentType.FACTUAL
        assert result.is_verifiable is True
        assert result.verdict is None

    @pytest.mark.parametrize("text", OPINION_SAMPLES)
    def test_opinion_samples_classified_as_opinion(self, text: str) -> None:
        """Verify subjective evaluations and viewpoints are categorized as OPINION."""
        result = classifier.classify(text)
        assert result.content_type == ContentType.OPINION
        assert result.is_verifiable is False
        assert result.verdict == VerdictType.VIEWPOINT

    @pytest.mark.parametrize("text", PREDICTION_SAMPLES)
    def test_prediction_samples_classified_as_prediction(self, text: str) -> None:
        """Verify forward-looking speculations are categorized as PREDICTION."""
        result = classifier.classify(text)
        assert result.content_type == ContentType.PREDICTION
        assert result.is_verifiable is False
        assert result.verdict == VerdictType.FUTURE_LOOKING

    @pytest.mark.parametrize("text", HYPOTHETICAL_SAMPLES)
    def test_hypothetical_samples_classified_as_hypothetical(self, text: str) -> None:
        """Verify counterfactual conditional scenarios are categorized as HYPOTHETICAL."""
        result = classifier.classify(text)
        assert result.content_type == ContentType.HYPOTHETICAL
        assert result.is_verifiable is False
        assert result.verdict == VerdictType.SCENARIO

    @pytest.mark.parametrize("text", CREATIVE_SAMPLES)
    def test_creative_samples_classified_as_creative(self, text: str) -> None:
        """Verify fiction, poetry, and storytelling are categorized as CREATIVE."""
        result = classifier.classify(text)
        assert result.content_type == ContentType.CREATIVE
        assert result.is_verifiable is False
        assert result.verdict == VerdictType.CREATIVE

    @pytest.mark.parametrize("text", INSTRUCTION_SAMPLES)
    def test_instruction_samples_classified_as_instruction(self, text: str) -> None:
        """Verify directives, imperatives, and how-tos are categorized as INSTRUCTION."""
        result = classifier.classify(text)
        assert result.content_type == ContentType.INSTRUCTION
        assert result.is_verifiable is False
        assert result.verdict == VerdictType.INCONCLUSIVE

    @pytest.mark.parametrize(
        "paragraph",
        [
            (
                "Paris is the capital of France. The Eiffel Tower stands 330 meters tall. "
                "The Louvre museum houses the Mona Lisa."
            ),
            (
                "Albert Einstein developed relativity in 1905. He received the Nobel Prize in 1921. "
                "He was born in Ulm, Germany."
            ),
            (
                "Water freezes at 0 degrees Celsius. It boils at 100 degrees Celsius under standard pressure. "
                "Liquid water expands when frozen into ice."
            ),
            (
                "The Moon orbits Earth every 27.3 days. Neil Armstrong walked on the lunar surface. "
                "The Apollo program completed six successful lunar landings."
            ),
            (
                "Python is a dynamic programming language. It supports multiple programming paradigms. "
                "Guido van Rossum released Python in 1991."
            ),
        ],
    )
    def test_claim_extraction_character_offset_invariance(self, paragraph: str) -> None:
        """Verify character offset invariance: text[start:end] == claim_text exactly."""
        claims = extractor.extract(paragraph)
        assert len(claims) >= 2
        for claim in claims:
            extracted_slice = paragraph[claim.start_offset : claim.end_offset]
            assert extracted_slice == claim.text
            assert claim.start_offset >= 0
            assert claim.end_offset <= len(paragraph)
            assert claim.start_offset < claim.end_offset
