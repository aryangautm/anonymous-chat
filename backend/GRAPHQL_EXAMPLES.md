# GraphQL API Examples

This file contains practical examples for testing the Knowledge Module GraphQL API.

## 🔧 Setup

1. Start the server:
```bash
cd backend
uvicorn app.main:app --reload
```

2. Access GraphiQL: http://localhost:8000/api/graphql

3. (Optional) Add authentication header:
```json
{
  "Authorization": "Bearer YOUR_FIREBASE_TOKEN"
}
```

---

## 📖 Query Examples

### 1. Get All Knowledge Modules for a Persona

```graphql
query GetKnowledgeModules {
  knowledgeModules(personaId: "123e4567-e89b-12d3-a456-426614174000") {
    id
    personaId
    moduleType
    title
    content
    priority
    isActive
    metadata
    createdAt
    updatedAt
  }
}
```

**Response:**
```json
{
  "data": {
    "knowledgeModules": [
      {
        "id": "987f6543-e21b-45d3-c456-426614174000",
        "personaId": "123e4567-e89b-12d3-a456-426614174000",
        "moduleType": "bio",
        "title": "About Me",
        "content": {
          "text": "I am a software developer"
        },
        "priority": 5,
        "isActive": true,
        "metadata": null,
        "createdAt": "2025-10-13T12:00:00Z",
        "updatedAt": "2025-10-13T12:00:00Z"
      }
    ]
  }
}
```

---

### 2. Get Single Knowledge Module

```graphql
query GetKnowledgeModule {
  knowledgeModule(moduleId: "987f6543-e21b-45d3-c456-426614174000") {
    id
    title
    moduleType
    content
    priority
    isActive
  }
}
```

**Response:**
```json
{
  "data": {
    "knowledgeModule": {
      "id": "987f6543-e21b-45d3-c456-426614174000",
      "title": "About Me",
      "moduleType": "bio",
      "content": {
        "text": "I am a software developer"
      },
      "priority": 5,
      "isActive": true
    }
  }
}
```

---

## ✏️ Mutation Examples

### 1. Create a Bio Module

```graphql
mutation CreateBioModule {
  addKnowledgeModule(
    personaId: "123e4567-e89b-12d3-a456-426614174000"
    input: {
      moduleType: "bio"
      title: "About Me"
      content: {
        text: "I am a software developer passionate about AI and web development."
      }
      priority: 5
      isActive: true
    }
  ) {
    id
    title
    moduleType
    content
    createdAt
  }
}
```

---

### 2. Create a Q&A Module

```graphql
mutation CreateQnaModule {
  addKnowledgeModule(
    personaId: "123e4567-e89b-12d3-a456-426614174000"
    input: {
      moduleType: "qna"
      title: "Frequently Asked Questions"
      content: {
        pairs: [
          {
            question: "What technologies do you use?",
            answer: "I primarily use Python, FastAPI, React, and PostgreSQL."
          },
          {
            question: "What's your experience level?",
            answer: "I have 5 years of professional software development experience."
          }
        ]
      }
      priority: 8
      isActive: true
      metadata: {
        source: "manual_entry",
        tags: ["experience", "skills"]
      }
    }
  ) {
    id
    title
    moduleType
    content
    priority
  }
}
```

---

### 3. Create a Text Block Module

```graphql
mutation CreateTextBlock {
  addKnowledgeModule(
    personaId: "123e4567-e89b-12d3-a456-426614174000"
    input: {
      moduleType: "text_block"
      title: "Technical Skills"
      content: {
        text: """
        # Technical Skills
        
        ## Backend
        - Python (FastAPI, Django)
        - Node.js (Express)
        - PostgreSQL, MongoDB
        
        ## Frontend
        - React, TypeScript
        - Tailwind CSS
        - GraphQL
        
        ## DevOps
        - Docker, Kubernetes
        - AWS, GCP
        - CI/CD pipelines
        """
      }
      priority: 7
      isActive: true
    }
  ) {
    id
    title
    content
  }
}
```

---

### 4. Create a URL Source Module

```graphql
mutation CreateUrlSource {
  addKnowledgeModule(
    personaId: "123e4567-e89b-12d3-a456-426614174000"
    input: {
      moduleType: "url_source"
      title: "My Blog"
      content: {
        url: "https://myblog.com",
        description: "Personal blog with technical articles"
      }
      priority: 3
      isActive: true
      metadata: {
        last_scraped: null,
        scrape_frequency: "weekly"
      }
    }
  ) {
    id
    title
    content
    metadata
  }
}
```

---

### 5. Update a Knowledge Module

```graphql
mutation UpdateModule {
  updateKnowledgeModule(
    moduleId: "987f6543-e21b-45d3-c456-426614174000"
    input: {
      title: "Updated Title"
      content: {
        text: "Updated content here"
      }
      priority: 9
      isActive: true
    }
  ) {
    id
    title
    content
    priority
    updatedAt
  }
}
```

**Note:** Only include fields you want to update. Omitted fields keep their current values.

---

### 6. Deactivate a Module (Soft Delete)

```graphql
mutation DeactivateModule {
  updateKnowledgeModule(
    moduleId: "987f6543-e21b-45d3-c456-426614174000"
    input: {
      isActive: false
    }
  ) {
    id
    isActive
  }
}
```

---

### 7. Delete a Knowledge Module (Hard Delete)

```graphql
mutation DeleteModule {
  deleteKnowledgeModule(moduleId: "987f6543-e21b-45d3-c456-426614174000")
}
```

**Response:**
```json
{
  "data": {
    "deleteKnowledgeModule": true
  }
}
```

---

## 🔐 Authentication Examples

### With Bearer Token

Add to HTTP Headers in GraphiQL:
```json
{
  "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Then run any query/mutation normally.

---

## 📊 Complex Query Examples

### Get Only Active Modules (Filter in Application)

```graphql
query GetActiveModules {
  knowledgeModules(personaId: "123e4567-e89b-12d3-a456-426614174000") {
    id
    title
    moduleType
    isActive
    priority
  }
}
```

Currently returns all modules. You can filter `isActive: true` on the client side, or add a filter parameter to the query (future enhancement).

---

### Get Modules with Specific Fields Only

```graphql
query GetModuleTitles {
  knowledgeModules(personaId: "123e4567-e89b-12d3-a456-426614174000") {
    id
    title
    moduleType
  }
}
```

GraphQL returns only requested fields, reducing payload size.

---

## 🧪 Testing Workflow

### 1. Create a Test Persona
First, you'll need a persona ID. Either:
- Use an existing persona from your database
- Create one via REST API or directly in database

### 2. Create Knowledge Modules
Use the mutation examples above to create various module types.

### 3. Query the Modules
Use the query examples to retrieve and verify your data.

### 4. Update Modules
Test updates with various field combinations.

### 5. Delete Modules
Test both soft delete (isActive: false) and hard delete.

---

## ⚠️ Common Errors

### Error: "Authentication required"
```json
{
  "errors": [
    {
      "message": "Authentication required",
      "path": ["knowledgeModules"]
    }
  ]
}
```

**Solution:** 
- Add Bearer token to headers
- Or temporarily comment out authentication checks for testing

---

### Error: "Access denied"
```json
{
  "errors": [
    {
      "message": "Access denied",
      "path": ["addKnowledgeModule"]
    }
  ]
}
```

**Solution:** 
- Make sure the persona belongs to the authenticated user
- Check that the persona_id is correct

---

### Error: "Persona not found"
```json
{
  "errors": [
    {
      "message": "Persona not found",
      "path": ["addKnowledgeModule"]
    }
  ]
}
```

**Solution:** 
- Verify the persona_id exists in the database
- Check that you're using the correct UUID format

---

## 💡 Pro Tips

1. **Use Variables** for dynamic values:
```graphql
mutation CreateModule($personaId: UUID!, $input: KnowledgeModuleInput!) {
  addKnowledgeModule(personaId: $personaId, input: $input) {
    id
    title
  }
}
```

Variables (in separate panel):
```json
{
  "personaId": "123e4567-e89b-12d3-a456-426614174000",
  "input": {
    "moduleType": "bio",
    "title": "About Me",
    "content": {"text": "Hello World"}
  }
}
```

2. **Use Fragments** for reusable fields:
```graphql
fragment ModuleFields on KnowledgeModuleType {
  id
  title
  moduleType
  priority
  isActive
}

query GetModules {
  knowledgeModules(personaId: "...") {
    ...ModuleFields
  }
}
```

3. **Introspection** to explore the schema:
```graphql
{
  __schema {
    types {
      name
      kind
    }
  }
}
```

4. **Type Information** for a specific type:
```graphql
{
  __type(name: "KnowledgeModuleType") {
    name
    fields {
      name
      type {
        name
        kind
      }
    }
  }
}
```

---

## 🔄 Module Type Content Structures

Different module types expect different content structures:

### bio
```json
{
  "text": "Biography text here"
}
```

### qna
```json
{
  "pairs": [
    {"question": "...", "answer": "..."}
  ]
}
```

### text_block
```json
{
  "text": "Markdown or plain text",
  "format": "markdown"
}
```

### url_source
```json
{
  "url": "https://example.com",
  "description": "Optional description"
}
```

### document
```json
{
  "filename": "resume.pdf",
  "file_path": "/path/to/file",
  "document_type": "pdf"
}
```

### services
```json
{
  "services": [
    {
      "name": "Web Development",
      "description": "...",
      "price": "Contact for quote"
    }
  ]
}
```

### social_media
```json
{
  "platforms": [
    {"name": "GitHub", "url": "https://github.com/username"},
    {"name": "LinkedIn", "url": "https://linkedin.com/in/username"}
  ]
}
```

---

**Happy testing! 🚀**

