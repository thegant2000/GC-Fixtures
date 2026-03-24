from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader
