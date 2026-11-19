
from datetime import datetime
from typing import Optional


class Meeting:
    def __init__(
        self,
        meeting_id: int,
        date_time: datetime,
        location: str,
        title: Optional[str] = None,
        committee: Optional[str] = None,
        agenda_packet_url: Optional[str] = None,) -> None:

        self.__meeting_id: int = meeting_id
        self.__date_time: datetime = date_time
        self.__location: str = location
        self.__title: Optional[str] = title
        self.__committee: Optional[str] = committee
        self.__agenda_packet_url: Optional[str] = agenda_packet_url

    def is_valid(self) -> bool:
        # meeting is valid only if it has a date/time, and location.
        if not isinstance(self.__date_time, datetime):
            return False
        if self.__location is None:
            return False
        return True

    def is_duplicate_of(self, other: "Meeting") -> bool:
        pass


class Municipality:
    def __init__(self, municipality_id: int, name: str, source_url: str) -> None:
        self.__municipality_id: int = municipality_id
        self.__name: str = name
        self.__source_url: str = source_url

    def update_source(self, url: str) -> None:
        pass


class Summary:
    def __init__(
        self,
        sections: dict[str, str],
        status: str = "unpublished",
        last_generated: Optional[datetime] = None,) -> None:

        self.__sections: dict[str, str] = sections
        self.__status: str = status
        self.__last_generated: Optional[datetime] = last_generated

    def verify(self) -> None:
        pass

    def update_sections(self, sections: dict[str, str]) -> None:
        pass

    def is_published(self) -> bool:
        pass
