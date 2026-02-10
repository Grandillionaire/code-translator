"""
Complex OOP Example for Code Translator
Demonstrates handling of advanced Python patterns

This example shows:
- Abstract base classes
- Multiple inheritance (mixins)
- Decorators (property, classmethod, staticmethod)
- Context managers
- Type hints with generics
- Dataclasses

Expected translations should handle paradigm differences appropriately.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Iterator, Optional
from contextlib import contextmanager
from datetime import datetime
import logging

# Generic type variable
T = TypeVar('T')

# Logging mixin
class LoggingMixin:
    """Mixin that provides logging capabilities."""
    
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)
    
    def log_info(self, message: str) -> None:
        self.logger.info(f"[{self.__class__.__name__}] {message}")
    
    def log_error(self, message: str, exc: Optional[Exception] = None) -> None:
        self.logger.error(f"[{self.__class__.__name__}] {message}", exc_info=exc)


# Abstract base class
class Repository(ABC, Generic[T]):
    """Abstract repository pattern for data access."""
    
    @abstractmethod
    def get(self, id: int) -> Optional[T]:
        """Retrieve an item by ID."""
        pass
    
    @abstractmethod
    def save(self, item: T) -> T:
        """Save an item and return it."""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete an item by ID."""
        pass
    
    @abstractmethod
    def list_all(self) -> list[T]:
        """List all items."""
        pass


# Dataclass for entity
@dataclass
class Product:
    """Product entity with automatic __init__, __repr__, etc."""
    id: int
    name: str
    price: float
    category: str
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def display_price(self) -> str:
        return f"${self.price:.2f}"
    
    def apply_discount(self, percentage: float) -> 'Product':
        """Return new product with discounted price."""
        new_price = self.price * (1 - percentage / 100)
        return Product(
            id=self.id,
            name=self.name,
            price=new_price,
            category=self.category,
            tags=self.tags.copy(),
            created_at=self.created_at
        )


# Concrete implementation with mixin
class InMemoryProductRepository(Repository[Product], LoggingMixin):
    """In-memory implementation of product repository."""
    
    def __init__(self):
        self._store: dict[int, Product] = {}
        self._next_id = 1
    
    def get(self, id: int) -> Optional[Product]:
        product = self._store.get(id)
        if product:
            self.log_info(f"Retrieved product {id}: {product.name}")
        return product
    
    def save(self, item: Product) -> Product:
        if item.id == 0:
            item = Product(
                id=self._next_id,
                name=item.name,
                price=item.price,
                category=item.category,
                tags=item.tags,
                created_at=item.created_at
            )
            self._next_id += 1
        
        self._store[item.id] = item
        self.log_info(f"Saved product {item.id}: {item.name}")
        return item
    
    def delete(self, id: int) -> bool:
        if id in self._store:
            del self._store[id]
            self.log_info(f"Deleted product {id}")
            return True
        return False
    
    def list_all(self) -> list[Product]:
        return list(self._store.values())
    
    @classmethod
    def create_with_sample_data(cls) -> 'InMemoryProductRepository':
        """Factory method to create repository with sample data."""
        repo = cls()
        samples = [
            Product(0, "Laptop", 999.99, "Electronics", ["tech", "computer"]),
            Product(0, "Headphones", 149.99, "Electronics", ["audio", "tech"]),
            Product(0, "Coffee Mug", 12.99, "Kitchen", ["home"]),
        ]
        for product in samples:
            repo.save(product)
        return repo
    
    @staticmethod
    def validate_price(price: float) -> bool:
        """Static method to validate price."""
        return price >= 0
    
    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Context manager for transaction-like behavior."""
        backup = self._store.copy()
        try:
            yield
            self.log_info("Transaction committed")
        except Exception as e:
            self._store = backup
            self.log_error("Transaction rolled back", e)
            raise


# Usage example
def main():
    # Create repository with sample data
    repo = InMemoryProductRepository.create_with_sample_data()
    
    # List all products
    products = repo.list_all()
    print(f"Total products: {len(products)}")
    
    for product in products:
        print(f"  - {product.name}: {product.display_price}")
    
    # Use context manager for safe operations
    with repo.transaction():
        laptop = repo.get(1)
        if laptop:
            discounted = laptop.apply_discount(10)
            repo.save(discounted)
            print(f"Applied 10% discount to {laptop.name}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
