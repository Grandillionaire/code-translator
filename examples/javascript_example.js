/**
 * JavaScript Example for Code Translator
 * Demonstrates translation to Python
 *
 * Expected Python output:
 * ----------------------
 * import asyncio
 * from dataclasses import dataclass
 * from typing import Optional
 *
 * @dataclass
 * class User:
 *     id: int
 *     name: str
 *     email: str
 *     created_at: str
 *
 * class UserService:
 *     def __init__(self, api_url: str):
 *         self.api_url = api_url
 *         self._cache = {}
 *
 *     async def fetch_user(self, user_id: int) -> Optional[User]:
 *         if user_id in self._cache:
 *             return self._cache[user_id]
 *         
 *         async with aiohttp.ClientSession() as session:
 *             async with session.get(f"{self.api_url}/users/{user_id}") as response:
 *                 if response.status != 200:
 *                     return None
 *                 data = await response.json()
 *                 user = User(**data)
 *                 self._cache[user_id] = user
 *                 return user
 */

// User data class
class User {
    constructor(id, name, email, createdAt) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.createdAt = createdAt;
    }

    toJSON() {
        return {
            id: this.id,
            name: this.name,
            email: this.email,
            created_at: this.createdAt
        };
    }
}

// Service class for user operations
class UserService {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this._cache = new Map();
    }

    async fetchUser(userId) {
        // Check cache first
        if (this._cache.has(userId)) {
            return this._cache.get(userId);
        }

        try {
            const response = await fetch(`${this.apiUrl}/users/${userId}`);
            
            if (!response.ok) {
                return null;
            }

            const data = await response.json();
            const user = new User(
                data.id,
                data.name,
                data.email,
                data.created_at
            );

            // Cache the result
            this._cache.set(userId, user);
            return user;
        } catch (error) {
            console.error(`Failed to fetch user ${userId}:`, error);
            return null;
        }
    }

    async fetchMultipleUsers(userIds) {
        // Fetch multiple users in parallel
        const promises = userIds.map(id => this.fetchUser(id));
        const users = await Promise.all(promises);
        return users.filter(user => user !== null);
    }

    clearCache() {
        this._cache.clear();
    }
}

// Arrow function examples
const formatUserName = (user) => `${user.name} <${user.email}>`;

const filterActiveUsers = (users) => 
    users.filter(u => u.createdAt > '2024-01-01');

// Async IIFE example
(async () => {
    const service = new UserService('https://api.example.com');
    const user = await service.fetchUser(123);
    
    if (user) {
        console.log('Found user:', formatUserName(user));
    }
})();

module.exports = { User, UserService, formatUserName, filterActiveUsers };
