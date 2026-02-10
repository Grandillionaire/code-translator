"""
Python Example for Code Translator
Demonstrates translation to JavaScript

Expected JavaScript output:
--------------------------
function calculateStatistics(numbers) {
    if (!numbers || numbers.length === 0) {
        return { count: 0, sum: 0, average: null, min: null, max: null };
    }
    
    const count = numbers.length;
    const sum = numbers.reduce((a, b) => a + b, 0);
    const average = sum / count;
    const min = Math.min(...numbers);
    const max = Math.max(...numbers);
    
    return { count, sum, average, min, max };
}

const numbers = [1, 2, 3, 4, 5, 10, 20];
const stats = calculateStatistics(numbers);
console.log(`Stats: ${JSON.stringify(stats)}`);

// Filter even numbers
const evenNumbers = numbers.filter(n => n % 2 === 0);
console.log(`Even: ${evenNumbers}`);

// Square all numbers  
const squared = numbers.map(n => n ** 2);
console.log(`Squared: ${squared}`);
"""

from typing import Optional


def calculate_statistics(numbers: list[float]) -> dict:
    """Calculate basic statistics for a list of numbers."""
    if not numbers:
        return {
            "count": 0,
            "sum": 0,
            "average": None,
            "min": None,
            "max": None
        }
    
    count = len(numbers)
    total = sum(numbers)
    average = total / count
    minimum = min(numbers)
    maximum = max(numbers)
    
    return {
        "count": count,
        "sum": total,
        "average": average,
        "min": minimum,
        "max": maximum
    }


def main():
    # Sample data
    numbers = [1, 2, 3, 4, 5, 10, 20]
    
    # Calculate statistics
    stats = calculate_statistics(numbers)
    print(f"Stats: {stats}")
    
    # List comprehension - filter even numbers
    even_numbers = [n for n in numbers if n % 2 == 0]
    print(f"Even: {even_numbers}")
    
    # List comprehension - square all numbers
    squared = [n ** 2 for n in numbers]
    print(f"Squared: {squared}")


if __name__ == "__main__":
    main()
