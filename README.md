Thank you for providing access to your repository. Based on the available information, here's an updated **README.md** for your project:

---

```markdown
# pyAvExt

**pyAvExt** is a Python-based tool designed to search for flight tickets using the Travelpayouts Aviasales Data API. It allows users to find round-trip flights from Moscow (MOW) to various destinations in Japan, including Tokyo (TYO), Nagoya (NGO), and Osaka (OSA), within specified date ranges and criteria.

## Features

- **Flexible Trip Duration**: Search for trips lasting between 12 to 17 days.
- **Date Overlap Requirement**: Ensure that the trip overlaps with a specified date window (e.g., March 28 to April 9, 2025) by at least 2 days.
- **Price Filtering**: Retrieve flights priced under 65,000 RUB.
- **Transfer Limitation**: Include flights with fewer than 3 total transfers (combined for departure and return).
- **Destination Options**: Search flights to multiple Japanese cities: Tokyo, Nagoya, and Osaka.

## Requirements

- **Python 3.8+**
- **Travelpayouts API Token**: Obtain from [Travelpayouts](https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API).
- **Dependencies**: Install required Python packages using:
  ```bash
  pip install requests tqdm
  ```

## Usage

1. **Clone the Repository**:
   ```bash
   git clone https://gitlab.com/MirumeYato/pyAvExt.git
   cd pyAvExt
   ```

2. **Configure API Token**:
   - Open the script file (e.g., `fly_tickets.py`).
   - Replace `"YOUR_TOKEN_HERE"` with your actual Travelpayouts API token.

3. **Run the Script**:
   ```bash
   python fly_tickets.py
   ```

   The script will search for flights based on the defined criteria and display the results in the console.

## How It Works

1. **Generate Query Combinations**:
   - Iterate over the list of destinations.
   - For each destination, generate possible departure dates within the specified range (e.g., March 15 to April 7, 2025).
   - For each departure date, calculate possible return dates based on the trip duration (12 to 17 days).
   - Ensure that the trip duration overlaps with the specified date window by at least 2 days.

2. **API Requests**:
   - For each valid combination of destination, departure date, and return date, construct an API request to the Aviasales Data API.
   - Retrieve flight data, including price, number of transfers, airline information, and booking links.

3. **Filter and Display Results**:
   - Filter flights based on the specified criteria (price under 65,000 RUB and fewer than 3 total transfers).
   - Sort the results by price in ascending order.
   - Display the flight options in a user-friendly format, including details such as destination, price, trip dates, airline, flight numbers, departure and return times, total transfers, and a direct booking link.

## Example Output

```
✈️  Flights found under 65000 rub:

🔹 Option 1:
   - Destination: Tokyo (TYO)
   - Price: 45000 rub
   - Trip Dates: 2025-03-29 to 2025-04-10
   - Airline: Japan Airlines (Flight No: JL401)
   - Departure Time: 10:30 AM
   - Return Time: 8:00 PM
   - Total Transfers: 2
   - Ticket Link: https://www.aviasales.com/example-link
```

## Notes

- **API Rate Limits**: Be mindful of the API rate limits imposed by Travelpayouts. Avoid making excessive requests in a short period.
- **Data Currency**: The Aviasales Data API provides cached data based on user searches, which may not reflect real-time availability or pricing.
- **Error Handling**: The script includes basic error handling for network requests. Ensure that your API token is valid and that you have an active internet connection when running the script.

## License

This project is licensed under the MIT License.

```

---

Feel free to customize this README further to align with any additional details or specific instructions related to your project. 