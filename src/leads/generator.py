"""Fake lead generator for testing."""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


# Realistic names by country
FIRST_NAMES: Dict[str, List[str]] = {
    "US": ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
           "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica"],
    "GB": ["Oliver", "Amelia", "Harry", "Emily", "Jack", "Isla", "George", "Ava",
           "Noah", "Sophia", "William", "Isabella", "James", "Mia", "Charles", "Charlotte"],
    "DE": ["Maximilian", "Sophie", "Paul", "Maria", "Leon", "Anna", "Felix", "Laura",
           "Hans", "Emma", "Karl", "Katherine", "Otto", "Clara", "Friedrich", "Martha"],
    "FR": ["Louis", "Emma", "Hugo", "Léa", "Arthur", "Chloé", "Raphaël", "Manon",
           "Gabriel", "Clara", "Jules", "Camille", "Adam", "Sarah", "Victor", "Nathalie"],
    "JP": ["Haruto", "Yui", "Sota", "Hana", "Hayato", "Mei", "Ren", "Yuna",
           "Kaito", "Sakura", "Yuto", "Miyu", "Sota", "Hinata", "Takumi", "Aoi"],
    "ID": ["Muhammad", "Siti", "Budi", "Nur", "Agus", "Dewi", "Joko", "Rini",
           "Ahmad", "Fatimah", "Hendra", "Wati", "Dedi", "Sari", "Rudi", "Lina"],
    "TH": ["Phong", "Mali", "Nisit", "Suda", "Sakda", "Malee", "Kriangsak", "Pim",
           "Somchai", "Daeng", "Kham", "Nuan", "Somsak", "Noi", "Kriangsak", "Nittaya"],
    "MY": ["Muhammad", "Nur", "Ahmad", "Aisyah", "Mohd", "Hafizah", "Ali", "Zaharah",
           "Abu", "Fatimah", "Hassan", "Zainab", "Omar", "Aminah", "Ibrahim", "Siti"],
    "VN": ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu",
           "Dang", "Bui", "Do", "Ho", "Ngo", "Duong", "Ly", "Truong"],
    "BR": ["João", "Maria", "Pedro", "Ana", "Carlos", "Julia", "José", "Fernanda",
           "Antonio", "Carla", "Paulo", "Marcia", "Lucas", "Beatriz", "André", "Renata"],
    "MX": ["José", "María", "Juan", "Ana", "Miguel", "Isabel", "Carlos", "Carmen",
           "Luis", "Rosa", "Jorge", "Patricia", "Francisco", "Margarita", "Diego", "Sofía"],
    "IN": ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Pooja", "Arun", "Kavita",
           "Suresh", "Sunita", "Rajesh", "Neha", "Anil", "Meera", "Vijay", "Rita"],
    "PH": ["Juan", "Maria", "Pedro", "Juana", "Pablo", "Luz", "Andres", "Carmen",
           "Jose", "Teresa", "Ramon", "Fe", "Manuel", "Rosario", "Francisco", "Luzviminda"],
    "AU": ["Oliver", "Charlotte", "Noah", "Ava", "William", "Sophia", "James", "Mia",
           "Benjamin", "Isla", "Lucas", "Grace", "Henry", "Lily", "Mason", "Ella"],
}

LAST_NAMES: Dict[str, List[str]] = {
    "US": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
           "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Lee"],
    "GB": ["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Wilson", "Evans",
           "Thomas", "Roberts", "Walker", "Wright", "Robinson", "Thompson", "White", "Hughes"],
    "DE": ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
           "Schulz", "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf"],
    "FR": ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand",
           "Leroy", "Moreau", "Simon", "Laurent", "Michel", "Garcia", "Martinez", "Lopez"],
    "JP": ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Nakamura", "Kobayashi",
           "Saito", "Kato", "Yoshida", "Yamada", "Sasaki", "Yamamoto", "Ishikawa", "Hayashi"],
    "ID": ["Santoso", "Wijaya", "Susanto", "Dewi", "Pratiwi", "Utomo", "Setiawan", "Wulandari",
           "Purnomo", "Kusuma", "Nugroho", "Wibowo", "Saputra", "Kusumaningrum", "Hadi", "Prasetyo"],
    "TH": ["Sukhum", "Chamnankit", "Phuket", "Nakorn", "Silom", "Sathorn", "Rajdamnoen", "Pahonyothin",
           "Srinakharin", "Ramkhamhaeng", "Chaeng Watthana", "Ngam Wong", "Phet Kasem", "Watcharapol", "Debaratna", "Sirinak"],
    "MY": ["Ahmad", "Abu", "Ali", "Omar", "Hassan", "Hussain", "Ibrahim", "Ismail",
           "Mohd", "Yusof", "Yaacob", "Salleh", "Chee", "Lee", "Tan", "Lim"],
    "VN": ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu",
           "Dang", "Bui", "Do", "Ho", "Ngo", "Duong", "Ly", "Truong"],
    "BR": ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
           "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Rocha", "Almeida"],
    "MX": ["García", "Rodríguez", "Hernández", "López", "González", "Martínez", "Pérez", "Sánchez",
           "Ramírez", "Flores", "Rivera", "Gómez", "Díaz", "Reyes", "Morales", "Cruz"],
    "IN": ["Singh", "Kumar", "Sharma", "Patel", "Agarwal", "Gupta", "Jain", "Mehta",
           "Shah", "Prasad", "Reddy", "Nair", "Menon", "Iyer", "Rao", "Das"],
    "PH": ["Santos", "Cruz", "Mendoza", "Lopez", "Gonzalez", "Dela Cruz", "Rodriguez", "Martinez",
           "Hernandez", "Garcia", "Ramos", "Flores", "Aquino", "Reyes", "Sanchez", "Castro"],
    "AU": ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Anderson", "Thomas",
           "Jackson", "White", "Harris", "Martin", "Thompson", "Robinson", "Clark", "Lewis"],
}

# Cities by country
CITIES: Dict[str, List[str]] = {
    "US": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"],
    "GB": ["London", "Birmingham", "Manchester", "Glasgow", "Liverpool", "Leeds", "Sheffield", "Bristol"],
    "DE": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Düsseldorf", "Dortmund"],
    "FR": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier"],
    "JP": ["Tokyo", "Yokohama", "Osaka", "Nagoya", "Sapporo", "Fukuoka", "Kobe", "Kyoto"],
    "ID": ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Makassar", "Palembang", "Tangerang"],
    "TH": ["Bangkok", "Chiang Mai", "Pattaya", "Phuket", "Khon Kaen", "Nakhon Ratchasima", "Hat Yai", "Udon Thani"],
    "MY": ["Kuala Lumpur", "George Town", "Ipoh", "Johor Bahru", "Malacca", "Shah Alam", "Petaling Jaya", "Kota Kinabalu"],
    "VN": ["Ho Chi Minh City", "Hanoi", "Da Nang", "Hai Phong", "Can Tho", "Bien Hoa", "Nha Trang", "Hue"],
    "BR": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza", "Curitiba", "Manaus", "Recife"],
    "MX": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "León", "Juárez", "Zapopan"],
    "IN": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad"],
    "PH": ["Manila", "Quezon City", "Davao City", "Caloocan", "Cebu City", "Zamboanga", "Taguig", "Pasig"],
    "AU": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Canberra", "Newcastle"],
}

# States/regions
STATES: Dict[str, List[str]] = {
    "US": ["NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"],
    "GB": ["England", "Scotland", "Wales", "Northern Ireland"],
    "DE": ["Bayern", "Nordrhein-Westfalen", "Baden-Württemberg", "Niedersachsen", "Hessen"],
    "ID": ["DKI Jakarta", "Jawa Barat", "Jawa Timur", "Jawa Tengah", "Sumatera Utara"],
    "TH": ["Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Khon Kaen"],
}

# Common domains for email
EMAIL_DOMAINS: Dict[str, List[str]] = {
    "US": ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "mail.com"],
    "GB": ["gmail.com", "yahoo.co.uk", "hotmail.com", "outlook.com", "btinternet.com"],
    "DE": ["gmail.com", "web.de", "gmx.de", "yahoo.de", "hotmail.de"],
    "FR": ["gmail.com", "orange.fr", "wanadoo.fr", "hotmail.com", "yahoo.fr"],
    "JP": ["gmail.com", "yahoo.co.jp", "ezweb.ne.jp", "softbank.ne.jp", "docomo.ne.jp"],
    "ID": ["gmail.com", "yahoo.com", "hotmail.com", "telkom.net", "indosat.net"],
}


@dataclass
class LeadGeneratorConfig:
    """Configuration for lead generation."""
    country: str = "US"
    count: int = 100
    include_phone: bool = True
    include_address: bool = True
    include_company: bool = False
    age_range: tuple = (18, 65)
    gender: Optional[str] = None  # male, female, or None for random


class LeadGenerator:
    """
    Generate fake lead data for testing.

    Creates realistic-looking leads with:
    - Names matching the country's culture
    - Valid email formats
    - Plausible phone numbers
    - Real city/state combinations
    - Appropriate demographics
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._random = random.Random(seed)

    def generate(self, config: Optional[LeadGeneratorConfig] = None) -> Dict[str, Any]:
        """
        Generate a single fake lead.

        Args:
            config: Generation configuration

        Returns:
            Lead data dictionary
        """
        if config is None:
            config = LeadGeneratorConfig()

        country = config.country.upper()

        # Generate name
        first_names = FIRST_NAMES.get(country, FIRST_NAMES["US"])
        last_names = LAST_NAMES.get(country, LAST_NAMES["US"])

        first_name = self._random.choice(first_names)
        last_name = self._random.choice(last_names)

        # Gender
        if config.gender:
            gender = config.gender.lower()
        else:
            gender = self._random.choice(["male", "female"])

        # Generate age
        age = self._random.randint(config.age_range[0], config.age_range[1])

        # Generate email
        email = self._generate_email(first_name, last_name, country)

        # Generate phone
        phone = None
        if config.include_phone:
            phone = self._generate_phone(country)

        # Generate address
        address = None
        if config.include_address:
            address = self._generate_address(country)

        # Generate company
        company = None
        if config.include_company:
            company = self._generate_company()

        # Build lead
        lead = {
            "first_name": first_name,
            "last_name": last_name,
            "name": f"{first_name} {last_name}",
            "email": email,
            "age": age,
            "gender": gender,
            "country": country,
        }

        if phone:
            lead["phone"] = phone

        if address:
            lead.update(address)

        if company:
            lead["company"] = company

        # Add common fields
        lead["lead_id"] = str(uuid.uuid4())[:8].upper()
        lead["created_at"] = datetime.utcnow().isoformat()

        return lead

    def generate_batch(
        self,
        count: int,
        country: str = "US",
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple fake leads.

        Args:
            count: Number of leads to generate
            country: Country code
            **kwargs: Additional config options

        Returns:
            List of lead dictionaries
        """
        config = LeadGeneratorConfig(country=country, count=count, **kwargs)
        return [self.generate(config) for _ in range(count)]

    def _generate_email(
        self,
        first_name: str,
        last_name: str,
        country: str,
    ) -> str:
        """Generate realistic email address."""
        domains = EMAIL_DOMAINS.get(country, EMAIL_DOMAINS["US"])
        domain = self._random.choice(domains)

        # Various email patterns
        patterns = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}{self._random.randint(1, 99)}",
            f"{first_name[0].lower()}{last_name.lower()}",
            f"{first_name.lower()}_{last_name.lower()}",
        ]

        # Add some variation
        pattern = self._random.choice(patterns)
        if self._random.random() > 0.7:
            pattern += str(self._random.randint(1, 999))

        return f"{pattern}@{domain}"

    def _generate_phone(self, country: str) -> str:
        """Generate plausible phone number."""
        if country == "US":
            area_codes = ["212", "310", "415", "312", "617", "202", "305", "206"]
            area_code = self._random.choice(area_codes)
            exchange = self._random.randint(200, 999)
            subscriber = self._random.randint(1000, 9999)
            return f"+1-{area_code}-{exchange}-{subscriber}"

        elif country == "GB":
            return f"+44-{self._random.randint(1000, 9999)}-{self._random.randint(100000, 999999)}"

        elif country == "ID":
            return f"+62-{self._random.randint(800, 899)}-{self._random.randint(1000000, 9999999)}"

        elif country == "TH":
            return f"+66-{self._random.randint(80, 89)}-{self._random.randint(100000, 999999)}"

        elif country == "JP":
            return f"+81-{self._random.randint(70, 90)}-{self._random.randint(1000, 9999)}-{self._random.randint(1000, 9999)}"

        elif country == "MY":
            return f"+60-{self._random.randint(10, 19)}-{self._random.randint(10000000, 99999999)}"

        elif country == "VN":
            return f"+84-{self._random.randint(90, 99)}-{self._random.randint(1000000, 9999999)}"

        elif country == "AU":
            return f"+61-{self._random.randint(400, 499)}-{self._random.randint(100000, 999999)}"

        elif country == "PH":
            return f"+63-{self._random.randint(900, 999)}-{self._random.randint(1000000, 9999999)}"

        elif country == "IN":
            return f"+91-{self._random.randint(6000, 9999)}-{self._random.randint(1000000, 9999999)}"

        else:
            # Generic format
            return f"+1-{self._random.randint(200, 999)}-{self._random.randint(1000000, 9999999)}"

    def _generate_address(self, country: str) -> Optional[Dict[str, str]]:
        """Generate plausible address."""
        cities = CITIES.get(country, CITIES["US"])
        city = self._random.choice(cities)

        # Generate street
        street_numbers = self._random.randint(1, 9999)
        streets = ["Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Elm St", "Park Ave", "First St", "Second Ave"]
        street = f"{street_numbers} {self._random.choice(streets)}"

        # Zip/postal code
        if country == "US":
            zip_code = f"{self._random.randint(10000, 99999)}"
        elif country == "GB":
            zip_code = f"{self._random.randint(1, 99)}{self._random.choice(['AA', 'BB', 'CC'])} {self._random.randint(1, 9)}{self._random.randint(0, 9)}"
        elif country == "ID":
            zip_code = f"{self._random.randint(10000, 99999)}"
        elif country == "JP":
            zip_code = f"{self._random.randint(100, 999)}-{self._random.randint(1000, 9999)}"
        else:
            zip_code = str(self._random.randint(10000, 99999))

        return {
            "street": street,
            "city": city,
            "state": self._random.choice(STATES.get(country, ["State"])),
            "zip_code": zip_code,
        }

    def _generate_company(self) -> Dict[str, str]:
        """Generate company name."""
        prefixes = ["Global", "Tech", "Digital", "Prime", "Elite", "Apex", "Nova", "Summit"]
        suffixes = ["Solutions", "Systems", "Services", "Technologies", "Industries", "Group", "Corp", "Inc"]

        return {
            "company_name": f"{self._random.choice(prefixes)} {self._random.choice(suffixes)}",
            "job_title": self._random.choice(["Manager", "Director", "Engineer", "Analyst", "Consultant", "Specialist"]),
        }

    def export_to_file(
        self,
        filepath: str,
        count: int,
        country: str = "US",
        format: str = "json",
        **kwargs,
    ) -> int:
        """
        Generate leads and save to file.

        Args:
            filepath: Output file path
            count: Number of leads
            country: Country code
            format: Output format ('json', 'csv')
            **kwargs: Additional config options

        Returns:
            Number of leads generated
        """
        leads = self.generate_batch(count, country, **kwargs)

        if format == "json":
            with open(filepath, "w") as f:
                json.dump(leads, f, indent=2)
        elif format == "csv":
            import csv
            if leads:
                with open(filepath, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=leads[0].keys())
                    writer.writeheader()
                    writer.writerows(leads)

        logger.info(f"Generated {count} leads to {filepath}")
        return count
