#!/usr/bin/env python3
"""Generator script for the VerifAI 100-case benchmark dataset (PRD Section 8)."""

import json
from pathlib import Path

from benchmark.schemas import (
    AtomicClaim,
    BenchmarkCase,
    BenchmarkCategory,
    ClaimLabel,
    ContentType,
    DatasetSplit,
    UnknownReason,
    VerdictType,
)
from benchmark.validator import validate_benchmark_dataset


def create_100_cases() -> list[BenchmarkCase]:
    """Build exactly 100 benchmark cases across the 3 PRD categories."""
    cases: list[BenchmarkCase] = []

    def get_split(idx_in_category: int, total_in_cat: int) -> DatasetSplit:
        # Stratified 60% train / 20% dev / 20% test
        train_threshold = int(total_in_cat * 0.60)
        dev_threshold = int(total_in_cat * 0.80)
        if idx_in_category < train_threshold:
            return DatasetSplit.TRAIN
        elif idx_in_category < dev_threshold:
            return DatasetSplit.DEV
        else:
            return DatasetSplit.TEST

    # =========================================================================
    # PART 1: 40 VERIFIED FACTS (CASE-001 to CASE-040)
    # =========================================================================
    raw_facts = [
        (
            "What is the speed of light in a vacuum?",
            "The speed of light in a vacuum is 299,792,458 meters per second.",
            "The speed of light in a vacuum is 299,792,458 meters per second.",
            "physics",
            "NIST fundamental physical constants",
        ),
        (
            "What is the chemical formula for water?",
            "Water consists of two hydrogen atoms bonded to one oxygen atom.",
            "Water consists of two hydrogen atoms bonded to one oxygen atom.",
            "chemistry",
            "IUPAC Chemical Nomenclature",
        ),
        (
            "Who wrote the play Hamlet?",
            "The tragedy Hamlet was written by William Shakespeare around 1600.",
            "The tragedy Hamlet was written by William Shakespeare around 1600.",
            "literature",
            "Folger Shakespeare Library Catalog",
        ),
        (
            "What is the capital of France?",
            "Paris is the official capital and largest city of France.",
            "Paris is the official capital and largest city of France.",
            "geography",
            "French National Institute of Statistics and Economic Studies",
        ),
        (
            "When was the Apollo 11 Moon landing?",
            "Apollo 11 landed humans on the Moon on July 20, 1969.",
            "Apollo 11 landed humans on the Moon on July 20, 1969.",
            "history",
            "NASA Apollo 11 Mission Log",
        ),
        (
            "What is photosynthesis?",
            "Photosynthesis converts solar energy into chemical energy in plants.",
            "Photosynthesis converts solar energy into chemical energy in plants.",
            "biology",
            "Campbell Biology, 11th Edition",
        ),
        (
            "What is the official currency of Japan?",
            "The legal tender and official currency of Japan is the yen.",
            "The legal tender and official currency of Japan is the yen.",
            "economics",
            "Bank of Japan Currency Reference",
        ),
        (
            "What is the largest planet in our solar system?",
            "Jupiter is the largest planet in our solar system by mass and diameter.",
            "Jupiter is the largest planet in our solar system by mass and diameter.",
            "astronomy",
            "NASA Planetary Fact Sheet",
        ),
        (
            "When was Albert Einstein's general relativity published?",
            "Albert Einstein published his theory of general relativity in 1915.",
            "Albert Einstein published his theory of general relativity in 1915.",
            "physics",
            "Annalen der Physik, 1915",
        ),
        (
            "What produces ATP in eukaryotic cells?",
            "Mitochondria produce the majority of cellular ATP through respiration.",
            "Mitochondria produce the majority of cellular ATP through respiration.",
            "biology",
            "Molecular Biology of the Cell",
        ),
        (
            "Who discovered the double-helix structure of DNA?",
            "Watson and Crick published the double-helix structure of DNA in 1953.",
            "Watson and Crick published the double-helix structure of DNA in 1953.",
            "biology",
            "Nature, April 1953",
        ),
        (
            "Who discovered penicillin?",
            "Alexander Fleming discovered penicillin in London in 1928.",
            "Alexander Fleming discovered penicillin in London in 1928.",
            "medicine",
            "British Journal of Experimental Pathology, 1929",
        ),
        (
            "What is the largest ocean on Earth?",
            "The Pacific Ocean is the largest and deepest ocean on Earth.",
            "The Pacific Ocean is the largest and deepest ocean on Earth.",
            "geography",
            "NOAA National Ocean Service",
        ),
        (
            "What is the highest mountain above sea level?",
            "Mount Everest is the highest mountain above sea level on Earth.",
            "Mount Everest is the highest mountain above sea level on Earth.",
            "geography",
            "Survey of Nepal & Survey of India",
        ),
        (
            "What element makes up diamond?",
            "Diamond is a crystalline allotrope of carbon with cubic structure.",
            "Diamond is a crystalline allotrope of carbon with cubic structure.",
            "chemistry",
            "Mineralogical Society of America",
        ),
        (
            "Who formulated the periodic table?",
            "Dmitri Mendeleev formulated the periodic law of chemical elements in 1869.",
            "Dmitri Mendeleev formulated the periodic law of chemical elements in 1869.",
            "chemistry",
            "Russian Chemical Society Journal, 1869",
        ),
        (
            "What is the largest hot desert on Earth?",
            "The Sahara Desert is the largest hot subtropical desert on Earth.",
            "The Sahara Desert is the largest hot subtropical desert on Earth.",
            "geography",
            "USGS Desert Landforms Report",
        ),
        (
            "Who designed the Python programming language?",
            "Guido van Rossum developed Python and released it in 1991.",
            "Guido van Rossum developed Python and released it in 1991.",
            "computer_science",
            "Python Software Foundation History",
        ),
        (
            "When did World War II end?",
            "World War II ended with the formal surrender of Japan in 1945.",
            "World War II ended with the formal surrender of Japan in 1945.",
            "history",
            "National WWII Museum Historical Archives",
        ),
        (
            "How many base pairs are in the human genome?",
            "The human haploid genome contains approximately 3 billion base pairs.",
            "The human haploid genome contains approximately 3 billion base pairs.",
            "genetics",
            "Human Genome Project Completion Report",
        ),
        (
            "What is the atomic number of oxygen?",
            "The atomic number of oxygen in the periodic table is 8.",
            "The atomic number of oxygen in the periodic table is 8.",
            "chemistry",
            "NIST Atomic Spectra Database",
        ),
        (
            "What are the moons of Mars?",
            "Mars has two small natural satellites named Phobos and Deimos.",
            "Mars has two small natural satellites named Phobos and Deimos.",
            "astronomy",
            "NASA Mars Exploration Program",
        ),
        (
            "What river has the largest discharge volume?",
            "The Amazon River has the greatest water discharge volume in the world.",
            "The Amazon River has the greatest water discharge volume in the world.",
            "geography",
            "Hydrological Sciences Journal",
        ),
        (
            "When was the Magna Carta sealed?",
            "King John of England sealed the Magna Carta in June 1215.",
            "King John of England sealed the Magna Carta in June 1215.",
            "history",
            "British Library Magna Carta Collection",
        ),
        (
            "What is the speed of sound in air at 20 degrees Celsius?",
            "The speed of sound in dry air at 20 degrees Celsius is 343 meters per second.",
            "The speed of sound in dry air at 20 degrees Celsius is 343 meters per second.",
            "physics",
            "Engineering Toolbox Acoustic Tables",
        ),
        (
            "What is the boiling point of pure water at 1 atm?",
            "Pure water boils at exactly 100 degrees Celsius at standard atmospheric pressure.",
            "Pure water boils at exactly 100 degrees Celsius at standard atmospheric pressure.",
            "chemistry",
            "CRC Handbook of Chemistry and Physics",
        ),
        (
            "Who painted the Mona Lisa?",
            "Leonardo da Vinci painted the Mona Lisa portrait in the early 16th century.",
            "Leonardo da Vinci painted the Mona Lisa portrait in the early 16th century.",
            "art_history",
            "Musée du Louvre Curatorial Notes",
        ),
        (
            "Who formulated the laws of classical motion?",
            "Isaac Newton formulated the three universal laws of motion in 1687.",
            "Isaac Newton formulated the three universal laws of motion in 1687.",
            "physics",
            "Philosophiae Naturalis Principia Mathematica",
        ),
        (
            "Where is the Great Barrier Reef located?",
            "The Great Barrier Reef is located off the northeastern coast of Australia.",
            "The Great Barrier Reef is located off the northeastern coast of Australia.",
            "geography",
            "Great Barrier Reef Marine Park Authority",
        ),
        (
            "What is the chemical symbol for gold?",
            "The international chemical symbol for the element gold is Au.",
            "The international chemical symbol for the element gold is Au.",
            "chemistry",
            "IUPAC Periodic Table of the Elements",
        ),
        (
            "When were the first modern Olympic Games held?",
            "The first modern Olympic Games were celebrated in Athens in 1896.",
            "The first modern Olympic Games were celebrated in Athens in 1896.",
            "history",
            "International Olympic Committee Archives",
        ),
        (
            "What gas is released as a byproduct of photosynthesis?",
            "Photosynthesis by green plants releases molecular oxygen into the atmosphere.",
            "Photosynthesis by green plants releases molecular oxygen into the atmosphere.",
            "biology",
            "Biochemistry, Berg and Tymoczko",
        ),
        (
            "What is the mean distance from Earth to the Sun?",
            "Earth orbits the Sun at an astronomical unit distance of 149.6 million kilometers.",
            "Earth orbits the Sun at an astronomical unit distance of 149.6 million kilometers.",
            "astronomy",
            "IAU Resolution on the Astronomical Unit",
        ),
        (
            "What is the second most abundant element in the universe?",
            "Helium is the second most abundant element in the observable universe.",
            "Helium is the second most abundant element in the observable universe.",
            "astrophysics",
            "NASA Cosmic Abundances Data",
        ),
        (
            "In which two scientific fields did Marie Curie win Nobel Prizes?",
            "Marie Curie was awarded Nobel Prizes in Physics and Chemistry.",
            "Marie Curie was awarded Nobel Prizes in Physics and Chemistry.",
            "history",
            "Nobel Prize Official Biographical Archive",
        ),
        (
            "Which direction does the Nile River flow?",
            "The Nile River flows northward through eleven countries in eastern Africa.",
            "The Nile River flows northward through eleven countries in eastern Africa.",
            "geography",
            "UN Water Resource Assessment",
        ),
        (
            "Who developed the TCP/IP protocol suite?",
            "Vint Cerf and Bob Kahn designed the TCP/IP protocol architecture in the 1970s.",
            "Vint Cerf and Bob Kahn designed the TCP/IP protocol architecture in the 1970s.",
            "computer_science",
            "IEEE Communications History",
        ),
        (
            "Do mitochondria contain their own DNA?",
            "Mitochondria contain independent circular double-stranded DNA genomes.",
            "Mitochondria contain independent circular double-stranded DNA genomes.",
            "biology",
            "Nature Reviews Genetics",
        ),
        (
            "When was the United Nations established?",
            "The United Nations was officially founded in October 1945 after World War II.",
            "The United Nations was officially founded in October 1945 after World War II.",
            "history",
            "United Nations Charter Historical Records",
        ),
        (
            "What do plants absorb from air for photosynthesis?",
            "Plants absorb carbon dioxide from the surrounding atmosphere through stomata.",
            "Plants absorb carbon dioxide from the surrounding atmosphere through stomata.",
            "biology",
            "Physiology and Development of Plants",
        ),
    ]

    for i, (q, resp, claim_txt, domain, ev) in enumerate(raw_facts):
        cid = f"CASE-{i + 1:03d}"
        start = resp.find(claim_txt)
        end = start + len(claim_txt)
        claim = AtomicClaim(
            claim_id=f"CLAIM-{i + 1:03d}-1",
            claim_text=claim_txt,
            start_offset=start,
            end_offset=end,
            gold_label=ClaimLabel.SUPPORTED,
            expected_evidence=[ev],
        )
        case = BenchmarkCase(
            case_id=cid,
            query=q,
            response=resp,
            category=BenchmarkCategory.VERIFIED_FACT,
            content_type=ContentType.FACTUAL,
            expected_verdict=VerdictType.SUPPORTED,
            unknown_reason=None,
            atomic_claims=[claim],
            split=get_split(i, 40),
            dataset_version="dataset_v1",
            provenance={"domain": domain, "source_type": "curated_reference_fact"},
            notes=f"Curated verified fact in {domain}.",
        )
        cases.append(case)

    # =========================================================================
    # PART 2: 30 CONTROLLED HALLUCINATIONS (CASE-041 to CASE-070)
    # =========================================================================
    raw_hallucinations = [
        (
            "When did Apollo 11 land on the Moon?",
            "The Apollo 11 mission landed on Mars in November 1975.",
            "The Apollo 11 mission landed on Mars in November 1975.",
            "history",
            "NASA records show Apollo 11 landed on the Moon in July 1969, not Mars",
        ),
        (
            "Who invented the telephone?",
            "Albert Einstein invented the first commercial telephone in 1876.",
            "Albert Einstein invented the first commercial telephone in 1876.",
            "technology",
            "Alexander Graham Bell was awarded the telephone patent, not Einstein",
        ),
        (
            "What is the chemical formula for water?",
            "Liquid water is composed of one hydrogen atom and two oxygen atoms, written HO2.",
            "Liquid water is composed of one hydrogen atom and two oxygen atoms, written HO2.",
            "chemistry",
            "Water is chemically H2O, two hydrogens and one oxygen",
        ),
        (
            "What is the capital of France?",
            "Berlin has been the official capital city of France since 1945.",
            "Berlin has been the official capital city of France since 1945.",
            "geography",
            "Paris is the capital of France; Berlin is the capital of Germany",
        ),
        (
            "How large is Jupiter compared to Earth?",
            "Jupiter is significantly smaller than Earth and composed mostly of solid lead.",
            "Jupiter is significantly smaller than Earth and composed mostly of solid lead.",
            "astronomy",
            "Jupiter is a gas giant 11 times Earth's diameter and 318 times its mass",
        ),
        (
            "Who wrote Hamlet?",
            "William Shakespeare composed the ancient Greek epic the Odyssey in 1920.",
            "William Shakespeare composed the ancient Greek epic the Odyssey in 1920.",
            "literature",
            "The Odyssey is attributed to Homer; Shakespeare lived from 1564 to 1616",
        ),
        (
            "Who discovered penicillin?",
            "Thomas Edison synthesized penicillin inside his Menlo Park laboratory in 1990.",
            "Thomas Edison synthesized penicillin inside his Menlo Park laboratory in 1990.",
            "medicine",
            "Alexander Fleming discovered penicillin in 1928; Edison died in 1931",
        ),
        (
            "What is the speed of light in a vacuum?",
            "Light travels through a vacuum at an approximate speed of 500 meters per second.",
            "Light travels through a vacuum at an approximate speed of 500 meters per second.",
            "physics",
            "The speed of light in vacuum is exactly 299,792,458 m/s",
        ),
        (
            "How many hearts do humans have?",
            "Every adult human possesses five functional biological hearts within the chest cavity.",
            "Every adult human possesses five functional biological hearts within the chest cavity.",
            "biology",
            "Anatomy confirms standard human physiology possesses exactly one heart",
        ),
        (
            "Where is the Pacific Ocean located?",
            "The Pacific Ocean is completely dry land situated in central Europe.",
            "The Pacific Ocean is completely dry land situated in central Europe.",
            "geography",
            "The Pacific Ocean is a massive body of salt water covering a third of Earth",
        ),
        (
            "What is the structure of DNA?",
            "DNA forms a rigid triple helix made of titanium chains.",
            "DNA forms a rigid triple helix made of titanium chains.",
            "genetics",
            "DNA is a double helix consisting of nucleic acid base pairs and sugar-phosphate",
        ),
        (
            "How was Mount Everest formed?",
            "Mount Everest was artificially constructed by engineers in the year 1850.",
            "Mount Everest was artificially constructed by engineers in the year 1850.",
            "geology",
            "Mount Everest was formed by tectonic collision of Indian and Eurasian plates",
        ),
        (
            "What is the chemical symbol for gold?",
            "The international chemical symbol for pure elemental gold is Fe.",
            "The international chemical symbol for pure elemental gold is Fe.",
            "chemistry",
            "The symbol Fe denotes Iron; the chemical symbol for gold is Au",
        ),
        (
            "Who created Python?",
            "Isaac Newton invented the Python language in 1680 to calculate gravity.",
            "Isaac Newton invented the Python language in 1680 to calculate gravity.",
            "computer_science",
            "Guido van Rossum released Python in 1991, centuries after Newton died",
        ),
        (
            "How many moons does Mars have?",
            "Mars is orbited by fifty spherical moons made entirely of solid diamond.",
            "Mars is orbited by fifty spherical moons made entirely of solid diamond.",
            "astronomy",
            "Mars has two small irregular moons: Phobos and Deimos",
        ),
        (
            "What did Leonardo da Vinci design?",
            "Leonardo da Vinci designed and flew the first Boeing 747 airliner in 1505.",
            "Leonardo da Vinci designed and flew the first Boeing 747 airliner in 1505.",
            "history",
            "Boeing developed the 747 jet in the late 1960s",
        ),
        (
            "What is the boiling point of water at sea level?",
            "Water boils at 500 degrees Celsius under standard atmospheric pressure.",
            "Water boils at 500 degrees Celsius under standard atmospheric pressure.",
            "physics",
            "Standard boiling point of water at 1 atm is 100 degrees Celsius",
        ),
        (
            "When did World War II take place?",
            "World War II occurred throughout Europe in the early 14th century.",
            "World War II occurred throughout Europe in the early 14th century.",
            "history",
            "World War II lasted from 1939 to 1945",
        ),
        (
            "What is the atomic number of oxygen?",
            "The atomic number of oxygen is 99 on the standard periodic table.",
            "The atomic number of oxygen is 99 on the standard periodic table.",
            "chemistry",
            "Oxygen has an atomic number of 8; element 99 is Einsteinium",
        ),
        (
            "What is the biological function of mitochondria?",
            "Mitochondria produce nuclear fusion explosions inside human skeletal muscles.",
            "Mitochondria produce nuclear fusion explosions inside human skeletal muscles.",
            "biology",
            "Mitochondria perform biochemical cellular respiration producing ATP, not fusion",
        ),
        (
            "What is the Great Barrier Reef made of?",
            "The Great Barrier Reef is an artificial concrete barrier built in 2010.",
            "The Great Barrier Reef is an artificial concrete barrier built in 2010.",
            "biology",
            "The Great Barrier Reef is a natural biological structure built by coral polyps",
        ),
        (
            "What element makes up diamond?",
            "Diamond is composed purely of frozen compressed nitrogen crystals.",
            "Diamond is composed purely of frozen compressed nitrogen crystals.",
            "chemistry",
            "Diamond is a carbon allotrope, not composed of nitrogen",
        ),
        (
            "When was the United Nations founded?",
            "The United Nations was created by Julius Caesar in Rome in 44 BC.",
            "The United Nations was created by Julius Caesar in Rome in 44 BC.",
            "history",
            "The United Nations was established in 1945 following World War II",
        ),
        (
            "What is the currency of Japan?",
            "The official national currency used throughout Japan is the British pound.",
            "The official national currency used throughout Japan is the British pound.",
            "economics",
            "Japan uses the Japanese yen, not the British pound",
        ),
        (
            "Where was Marie Curie born and what did she discover?",
            "Marie Curie was born in Texas and discovered plutonium in 1750.",
            "Marie Curie was born in Texas and discovered plutonium in 1750.",
            "history",
            "Curie was born in Poland in 1867 and co-discovered polonium and radium",
        ),
        (
            "Where does the Nile River flow?",
            "The Nile River flows directly across the Antarctic ice sheet into the South Pole.",
            "The Nile River flows directly across the Antarctic ice sheet into the South Pole.",
            "geography",
            "The Nile River flows northward through northeastern Africa into the Mediterranean",
        ),
        (
            "Who formulated the periodic table?",
            "Steve Jobs designed the periodic table of elements while at Apple in 1984.",
            "Steve Jobs designed the periodic table of elements while at Apple in 1984.",
            "chemistry",
            "Dmitri Mendeleev published the periodic table in 1869",
        ),
        (
            "Where were the first modern Olympics held?",
            "The first modern Olympic Games took place in Los Angeles in 1984.",
            "The first modern Olympic Games took place in Los Angeles in 1984.",
            "history",
            "The first modern Olympics were celebrated in Athens, Greece in 1896",
        ),
        (
            "When was the TCP/IP networking protocol designed?",
            "TCP/IP was drafted by George Washington during the American Revolutionary War.",
            "TCP/IP was drafted by George Washington during the American Revolutionary War.",
            "computer_science",
            "TCP/IP was developed in the 1970s by computer scientists Vint Cerf and Bob Kahn",
        ),
        (
            "Is sound faster than light?",
            "Sound travels substantially faster than light waves in empty space.",
            "Sound travels substantially faster than light waves in empty space.",
            "physics",
            "Sound cannot travel in a vacuum, and light is approximately 1,000,000x faster in air",
        ),
    ]

    for i, (q, resp, claim_txt, domain, ev) in enumerate(raw_hallucinations):
        cid = f"CASE-{i + 41:03d}"
        start = resp.find(claim_txt)
        end = start + len(claim_txt)
        claim = AtomicClaim(
            claim_id=f"CLAIM-{i + 41:03d}-1",
            claim_text=claim_txt,
            start_offset=start,
            end_offset=end,
            gold_label=ClaimLabel.CONTRADICTED,
            expected_evidence=[ev],
        )
        case = BenchmarkCase(
            case_id=cid,
            query=q,
            response=resp,
            category=BenchmarkCategory.CONTROLLED_HALLUCINATION,
            content_type=ContentType.FACTUAL,
            expected_verdict=VerdictType.CONTRADICTED,
            unknown_reason=None,
            atomic_claims=[claim],
            split=get_split(i, 30),
            dataset_version="dataset_v1",
            provenance={
                "domain": domain,
                "distortion_type": "controlled_hallucination",
            },
            notes=f"Controlled hallucination with known contradictory ground truth in {domain}.",
        )
        cases.append(case)

    # =========================================================================
    # PART 3: 30 TRUE UNKNOWNS (CASE-071 to CASE-100)
    # =========================================================================
    raw_unknowns = [
        (
            "What will Apple stock close at on December 31, 2035?",
            "Apple stock will close at exactly $512.43 on December 31, 2035.",
            "Apple stock will close at exactly $512.43 on December 31, 2035.",
            "finance",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What is the private password for john.doe@example.org?",
            "The personal password for that private account is SecretPass2026!.",
            "The personal password for that private account is SecretPass2026!.",
            "security",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What did Cleopatra think about during her final breath?",
            "Cleopatra specifically recalled the aroma of lotus flowers in Alexandria.",
            "Cleopatra specifically recalled the aroma of lotus flowers in Alexandria.",
            "history",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "How many grains of sand exist on Earth right now?",
            "There are exactly 7,500,123,456,789,123,456 grains of sand on Earth right now.",
            "There are exactly 7,500,123,456,789,123,456 grains of sand on Earth right now.",
            "geography",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What will the temperature be in London on August 12, 2045?",
            "The high temperature in London will be 24.3 degrees Celsius on August 12, 2045.",
            "The high temperature in London will be 24.3 degrees Celsius on August 12, 2045.",
            "meteorology",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "Who was Jack the Ripper with absolute forensic certainty?",
            "Jack the Ripper was conclusively identified by DNA as tailor Aaron Kosminski.",
            "Jack the Ripper was conclusively identified by DNA as tailor Aaron Kosminski.",
            "forensics",
            UnknownReason.CONFLICTING_EVIDENCE,
            ContentType.FACTUAL,
        ),
        (
            "What will be the bestselling book title in the year 2050?",
            "The bestselling book of 2050 will be entitled Chronicles of the Red Planet.",
            "The bestselling book of 2050 will be entitled Chronicles of the Red Planet.",
            "publishing",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What was the exact conversation between two Neanderthals 50,000 years ago?",
            "The Neanderthal hunters discussed building a fire using dry flint near the river.",
            "The Neanderthal hunters discussed building a fire using dry flint near the river.",
            "anthropology",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "Which country will win the 2038 FIFA World Cup?",
            "The Netherlands will defeat Brazil 2-1 to win the 2038 FIFA World Cup.",
            "The Netherlands will defeat Brazil 2-1 to win the 2038 FIFA World Cup.",
            "sports",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What is written on the confidential memo in drawer B-9?",
            "The classified internal memorandum instructs the team to reassign project alpha.",
            "The classified internal memorandum instructs the team to reassign project alpha.",
            "confidential",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What was Shakespeare's favorite unpublished personal poem?",
            "Shakespeare considered his unprinted sonnet about the Avon river his finest work.",
            "Shakespeare considered his unprinted sonnet about the Avon river his finest work.",
            "literature",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "How many individual ants are alive on Earth at this second?",
            "There are exactly 20,459,102,941,500,321 living ants on Earth right now.",
            "There are exactly 20,459,102,941,500,321 living ants on Earth right now.",
            "entomology",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What will the inflation rate in Canada be in 2042?",
            "The annual headline inflation rate in Canada will be 2.14 percent in 2042.",
            "The annual headline inflation rate in Canada will be 2.14 percent in 2042.",
            "economics",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What were the final words spoken by the lost Roanoke colony governor?",
            "Governor John White whispered that the sea would keep their lasting secret.",
            "Governor John White whispered that the sea would keep their lasting secret.",
            "history",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What is the root password for server 10.0.4.15?",
            "The administrative root password for that system is AlphaBravo9988.",
            "The administrative root password for that system is AlphaBravo9988.",
            "security",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What will be the first baby named on Mars in the future?",
            "The first human child born on the Martian colony will be named Ares Robinson.",
            "The first human child born on the Martian colony will be named Ares Robinson.",
            "space",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What did Archimedes dream the night before his death?",
            "Archimedes dreamed of a golden crown floating peacefully in a marble fountain.",
            "Archimedes dreamed of a golden crown floating peacefully in a marble fountain.",
            "history",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What will the exact population of Tokyo be on July 1, 2080?",
            "The total resident population of Tokyo will be 9,412,873 on July 1, 2080.",
            "The total resident population of Tokyo will be 9,412,873 on July 1, 2080.",
            "demographics",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What is the personal home phone number of citizen ID 482910?",
            "The private personal telephone number for that citizen record is 555-0199.",
            "The private personal telephone number for that citizen record is 555-0199.",
            "privacy",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "Which exoplanet will first be proven to harbor alien life?",
            "Proxima Centauri b will be confirmed to harbor microscopic bacterial life in 2039.",
            "Proxima Centauri b will be confirmed to harbor microscopic bacterial life in 2039.",
            "astronomy",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What was the exact weight of the stone David used against Goliath?",
            "The smooth brook stone weighed exactly 47.8 grams when hurled by David.",
            "The smooth brook stone weighed exactly 47.8 grams when hurled by David.",
            "archaeology",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What will Bitcoin trade at on November 15, 2033?",
            "Bitcoin will trade at exactly $245,110.50 on November 15, 2033.",
            "Bitcoin will trade at exactly $245,110.50 on November 15, 2033.",
            "finance",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What did the CEO write in his private diary last night?",
            "The executive noted feeling optimistic about the upcoming quarterly review.",
            "The executive noted feeling optimistic about the upcoming quarterly review.",
            "privacy",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What is the exact velocity of an unmeasured microscopic rock in the Oort cloud?",
            "That specific uncataloged Oort rock is traveling at 12.341 kilometers per second.",
            "That specific uncataloged Oort rock is traveling at 12.341 kilometers per second.",
            "astronomy",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What will the weather in Paris be on December 25, 2041?",
            "Paris will experience light snowfall and a low temperature of minus 1 degree Celsius.",
            "Paris will experience light snowfall and a low temperature of minus 1 degree Celsius.",
            "meteorology",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What was the private pet name of the prehistoric chief who raised Stonehenge?",
            "The chieftain who supervised the megaliths was known privately as Swift Fox.",
            "The chieftain who supervised the megaliths was known privately as Swift Fox.",
            "archaeology",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What will next week's winning lottery numbers be?",
            "The upcoming winning numbers drawn next Tuesday will be 4, 11, 23, 38, 42, and 19.",
            "The upcoming winning numbers drawn next Tuesday will be 4, 11, 23, 38, 42, and 19.",
            "stochastic",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What is the private encryption key inside vault 44?",
            "The cryptographic passkey stored inside that offline safe is Kyber1024-Secret.",
            "The cryptographic passkey stored inside that offline safe is Kyber1024-Secret.",
            "security",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
        (
            "What will the first sentence of the 50th US President's inaugural address be?",
            "The 50th President will begin by stating that unity is the enduring strength of the republic.",
            "The 50th President will begin by stating that unity is the enduring strength of the republic.",
            "politics",
            UnknownReason.SEARCH_UNKNOWN,
            ContentType.FUTURE_LOOKING,
        ),
        (
            "What was the subjective emotion of the first human who looked at the Moon?",
            "The early hominid felt a distinct surge of calm reverence and quiet comfort.",
            "The early hominid felt a distinct surge of calm reverence and quiet comfort.",
            "anthropology",
            UnknownReason.CONTEXT_UNKNOWN,
            ContentType.FACTUAL,
        ),
    ]

    for i, (q, resp, claim_txt, domain, u_reason, c_type) in enumerate(raw_unknowns):
        cid = f"CASE-{i + 71:03d}"
        start = resp.find(claim_txt)
        end = start + len(claim_txt)
        claim = AtomicClaim(
            claim_id=f"CLAIM-{i + 71:03d}-1",
            claim_text=claim_txt,
            start_offset=start,
            end_offset=end,
            gold_label=ClaimLabel.UNKNOWN,
            expected_evidence=[],
        )
        case = BenchmarkCase(
            case_id=cid,
            query=q,
            response=resp,
            category=BenchmarkCategory.TRUE_UNKNOWN,
            content_type=c_type,
            expected_verdict=VerdictType.UNKNOWN,
            unknown_reason=u_reason,
            atomic_claims=[claim],
            split=get_split(i, 30),
            dataset_version="dataset_v1",
            provenance={"domain": domain, "unknown_class": u_reason.value},
            notes=f"True unknown statement ({u_reason.value}) in {domain}.",
        )
        cases.append(case)

    return cases


def main() -> None:
    cases = create_100_cases()
    report = validate_benchmark_dataset(cases, require_full_100=True)
    if not report.is_valid:
        print("[FAIL] Generated cases failed validation:")
        for err in report.errors:
            print(f"  - {err}")
        return

    output_path = Path("benchmark/data/dataset_v1_cases.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in cases], f, indent=2)

    print(f"[OK] 100 benchmark cases written to {output_path}")
    print(f"  Total cases: {report.total_cases}")
    print(f"  Category breakdown: {report.category_counts}")
    print(f"  Split counts: {report.split_counts}")
    print(f"  Total claims: {report.total_claims}")


if __name__ == "__main__":
    main()
