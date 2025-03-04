# OpenSentiment

## Quick Start with Docker

### Prerequisites
- Docker
- Docker Compose

### Setup and Run
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/opensentiment.git
   cd opensentiment
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. The API will be available at http://localhost:8000

### Development
- Source code changes in the `src` directory will be reflected immediately due to volume mounting
- View logs: `docker-compose logs -f api`
- Stop services: `docker-compose down`
- Rebuild after dependency changes: `docker-compose up -d --build`

### Production Deployment
1. Copy the environment file and set secure values:
   ```bash
   cp .env.example .env
   # Edit .env with secure production values
   ```

2. Start the production services:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

Key differences in production:
- Enhanced security with environment variables
- Resource limits and reservations
- Health checks for all services
- Automatic restarts
- Debug mode disabled

### Database Sharding Architecture

The production setup uses Citus (distributed PostgreSQL) to handle large datasets efficiently:

1. **Node Structure**:
   - 1 Coordinator Node: Manages distributed queries and stores metadata
   - 2 Worker Nodes: Store and process data in parallel
   - Easily scalable by adding more worker nodes

2. **Data Distribution**:
   - Sentiment results sharded by `batch_id` for efficient batch processing
   - Source data distributed by `source_id`
   - Political categories replicated across all nodes as reference data

3. **Performance Features**:
   - Parallel query execution
   - Distributed joins
   - Automatic sharding
   - Index support on sharded tables

4. **Scaling the Database**:
   To add more worker nodes:
   ```bash
   # 1. Add new worker service in docker-compose.prod.yml
   # 2. Connect to coordinator node:
   docker-compose exec db-coordinator psql -U ${DB_USER} -d ${DB_NAME}
   # 3. Add the new node:
   SELECT citus_add_node('db-worker-n', 5432);
   ```

## Scaling Strategy

1. **Horizontal Scaling**
   - Containerized microservices
   - Regional deployment
   - Load balancing

2. **Data Management**
   - Sharded database
   - Content caching
   - CDN integration

3. **Processing**
   - Async job queues
   - Batch processing
   - Priority queuing

## Community Engagement Levels

1. **Core Developers**
   - Platform development
   - Model optimization
   - Infrastructure management

2. **Domain Experts**
   - Model training and validation
   - Content classification guidelines
   - Quality control processes

3. **Content Reviewers**
   - Manual content review
   - Source verification
   - Bias assessment

4. **General Users**
   - Content submission
   - Feedback
   - Basic annotations

## Sustainability Model

1. **Open Source Foundation**
   - Community governance
   - Transparent decision making
   - Open development

2. **Funding Sources**
   - Research grants
   - Corporate sponsorships
   - Premium API access
   - Community donations

3. **Resource Management**
   - Cloud infrastructure optimization
   - Volunteer contribution coordination
   - Partnership programs

## Development Roadmap

### Phase 1: Core Infrastructure
- Basic API implementation
- Initial model integration
- Database setup
- Basic authentication

### Phase 2: Scaling
- Distributed architecture
- Multiple model support
- Advanced caching
- Performance optimization

### Phase 3: Community
- User management
- Contribution system
- Quality control workflows
- Documentation

### Phase 4: Advanced Features
- Model comparison tools
- Advanced analytics
- API integrations
- Mobile SDK

## Contributing

See https://opensentiment.org/docs/project/contribute/ for detailed information on how to contribute to OpenSentiment.

