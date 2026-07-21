import { useEffect, useMemo, useRef, useState } from "react";
import { Bell, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface SearchItem {
  name: string;
  path: string;
  keywords: string[];
}

const searchItems: SearchItem[] = [
  {
    name: "Dashboard",
    path: "/",
    keywords: ["dashboard", "home", "overview", "summary"],
  },
  {
    name: "Plant Map",
    path: "/plant-map",
    keywords: ["plant", "map", "zone", "zones", "location"],
  },
  {
    name: "Workers & PPE",
    path: "/workers",
    keywords: ["worker", "workers", "ppe", "helmet", "safety"],
  },
  {
    name: "Incidents",
    path: "/incidents",
    keywords: ["incident", "incidents", "alert", "accident"],
  },
  {
    name: "Emergency Response",
    path: "/emergency",
    keywords: ["emergency", "response", "evacuation", "responder"],
  },
  {
    name: "Permit Management",
    path: "/permits",
    keywords: [
      "permit",
      "permits",
      "hot work",
      "confined space",
      "gas test",
      "isolation",
    ],
  },
  {
    name: "Maintenance",
    path: "/maintenance",
    keywords: [
      "maintenance",
      "equipment",
      "machine",
      "work order",
      "repair",
    ],
  },
  {
    name: "Risk Intelligence",
    path: "/risk",
    keywords: [
      "risk",
      "critical",
      "hazard",
      "prediction",
      "recommendation",
    ],
  },
  {
    name: "Analytics",
    path: "/analytics",
    keywords: [
      "analytics",
      "chart",
      "charts",
      "graph",
      "statistics",
      "trend",
    ],
  },
];

function Header() {
  const navigate = useNavigate();

  const [searchText, setSearchText] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const searchWrapperRef = useRef<HTMLDivElement>(null);

  const filteredItems = useMemo(() => {
    const normalizedSearch = searchText.trim().toLowerCase();

    if (!normalizedSearch) {
      return [];
    }

    return searchItems.filter((item) => {
      const searchableText = [
        item.name,
        ...item.keywords,
      ]
        .join(" ")
        .toLowerCase();

      return searchableText.includes(normalizedSearch);
    });
  }, [searchText]);

  const openPage = (item: SearchItem) => {
    navigate(item.path);
    setSearchText("");
    setIsSearchOpen(false);
    setSelectedIndex(0);
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    if (!isSearchOpen || filteredItems.length === 0) {
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();

      setSelectedIndex((currentIndex) =>
        currentIndex === filteredItems.length - 1
          ? 0
          : currentIndex + 1,
      );
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();

      setSelectedIndex((currentIndex) =>
        currentIndex === 0
          ? filteredItems.length - 1
          : currentIndex - 1,
      );
    }

    if (event.key === "Enter") {
      event.preventDefault();

      const selectedItem = filteredItems[selectedIndex];

      if (selectedItem) {
        openPage(selectedItem);
      }
    }

    if (event.key === "Escape") {
      setIsSearchOpen(false);
    }
  };

  useEffect(() => {
    setSelectedIndex(0);
  }, [searchText]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchWrapperRef.current &&
        !searchWrapperRef.current.contains(event.target as Node)
      ) {
        setIsSearchOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <header className="header">
      <div
        className="search-wrapper"
        ref={searchWrapperRef}
      >
        <div className="search-container">
          <Search size={19} />

          <input
            type="text"
            value={searchText}
            placeholder="Search zones, incidents, workers or permits..."
            onChange={(event) => {
              setSearchText(event.target.value);
              setIsSearchOpen(true);
            }}
            onFocus={() => {
              if (searchText.trim()) {
                setIsSearchOpen(true);
              }
            }}
            onKeyDown={handleKeyDown}
          />
        </div>

        {isSearchOpen && searchText.trim() && (
          <div className="search-results">
            {filteredItems.length > 0 ? (
              filteredItems.map((item, index) => (
                <button
                  type="button"
                  key={item.path}
                  className={`search-result-item ${
                    selectedIndex === index
                      ? "search-result-item-active"
                      : ""
                  }`}
                  onMouseEnter={() => setSelectedIndex(index)}
                  onClick={() => openPage(item)}
                >
                  <Search size={15} />

                  <div>
                    <strong>{item.name}</strong>
                    <span>Open {item.name}</span>
                  </div>
                </button>
              ))
            ) : (
              <div className="search-empty-result">
                No matching page found
              </div>
            )}
          </div>
        )}
      </div>

      <div className="header-actions">
        <button className="notification-button" type="button">
          <Bell size={20} />
          <span className="notification-dot" />
        </button>

        <div className="profile">
          <div className="profile-avatar">SO</div>

          <div>
            <strong>Safety Officer</strong>
            <p>Plant Administrator</p>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;