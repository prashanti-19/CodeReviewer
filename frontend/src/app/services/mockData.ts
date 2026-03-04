import { Finding, AnalysisResults } from '../types/analysis';

// Mock findings data - structured exactly like the real API will return
export const mockFindings: Finding[] = [
  {
    id: '1',
    file: 'src/auth/login.py',
    line_start: 42,
    line_end: 47,
    category: 'security',
    severity: 'critical',
    rule: 'hardcoded-credentials',
    title: 'Hardcoded API Key Detected',
    description: 'These lines contain a hardcoded API key, which exposes credentials in source control and makes rotation difficult. API keys should be stored in environment variables or a secure secrets management system.',
    snippet: `def authenticate_user(username, password):
    # SECURITY ISSUE: Hardcoded credentials
    API_KEY = 'sk-live-abc123def456ghi789'
    SECRET_TOKEN = 'prod_secret_key_xyz'
    
    headers = {'Authorization': f'Bearer {API_KEY}'}
    return make_request(headers)`
  },
  {
    id: '2',
    file: 'src/utils/database.py',
    line_start: 156,
    line_end: 158,
    category: 'security',
    severity: 'high',
    rule: 'sql-injection',
    title: 'SQL Injection Vulnerability',
    description: 'This code constructs SQL queries using string concatenation with user input, making it vulnerable to SQL injection attacks. Use parameterized queries or an ORM instead.',
    snippet: `def get_user_data(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return db.execute(query)`
  },
  {
    id: '3',
    file: 'src/components/UserProfile.jsx',
    line_start: 23,
    line_end: 26,
    category: 'security',
    severity: 'high',
    rule: 'xss-vulnerability',
    title: 'Cross-Site Scripting (XSS) Risk',
    description: 'Using dangerouslySetInnerHTML with unsanitized user input can lead to XSS attacks. Always sanitize HTML content or use safe rendering methods.',
    snippet: `function UserProfile({ userData }) {
  return (
    <div dangerouslySetInnerHTML={{ __html: userData.bio }} />
  );
}`
  },
  {
    id: '4',
    file: 'src/services/payment.py',
    line_start: 89,
    line_end: 145,
    category: 'code-smell',
    severity: 'high',
    rule: 'long-method',
    title: 'Excessively Long Method',
    description: 'This method spans 57 lines and handles multiple responsibilities including validation, payment processing, logging, and email notifications. Consider breaking it into smaller, focused methods.',
    snippet: `def process_payment(self, user_id, amount, card_info):
    # Validate user
    user = self.db.query(User).filter_by(id=user_id).first()
    if not user:
        raise ValueError("User not found")
    
    # Validate amount
    if amount <= 0:
        raise ValueError("Invalid amount")
    
    # ... 40+ more lines of mixed concerns ...`
  },
  {
    id: '5',
    file: 'src/models/OrderManager.java',
    line_start: 1,
    line_end: 15,
    category: 'code-smell',
    severity: 'medium',
    rule: 'god-class',
    title: 'God Class Anti-Pattern',
    description: 'This class has 847 lines and handles order processing, inventory management, customer notifications, payment processing, and reporting. Consider splitting into focused, single-responsibility classes.',
    snippet: `public class OrderManager {
    private Database db;
    private EmailService emailer;
    private PaymentGateway gateway;
    private InventorySystem inventory;
    private ReportGenerator reports;
    private AuditLogger logger;
    
    // 847 lines of mixed responsibilities...
    public void processOrder() { /* ... */ }
    public void updateInventory() { /* ... */ }
    public void sendNotifications() { /* ... */ }
    // ... dozens more methods ...
}`
  },
  {
    id: '6',
    file: 'src/utils/helpers.js',
    line_start: 234,
    line_end: 239,
    category: 'code-smell',
    severity: 'medium',
    rule: 'duplicated-code',
    title: 'Duplicated Logic Detected',
    description: 'This validation logic is duplicated in 7 different files. Extract it into a shared utility function to improve maintainability and reduce code duplication.',
    snippet: `function validateEmail(email) {
  if (!email) return false;
  if (email.length < 5) return false;
  if (!email.includes('@')) return false;
  if (!email.includes('.')) return false;
  return true;
}`
  },
  {
    id: '7',
    file: 'src/controllers/analytics.py',
    line_start: 67,
    line_end: 82,
    category: 'maintainability',
    severity: 'high',
    rule: 'high-complexity',
    title: 'High Cyclomatic Complexity',
    description: 'This function has a cyclomatic complexity of 23, making it difficult to test and maintain. The deeply nested if/else statements should be refactored into smaller functions or use early returns.',
    snippet: `def calculate_metrics(data, options):
    if data:
        if options.get('type') == 'sales':
            if options.get('period') == 'monthly':
                if data.get('revenue'):
                    if data['revenue'] > 0:
                        # ... 10 more levels of nesting ...
                        return result
    return None`
  },
  {
    id: '8',
    file: 'src/config/constants.ts',
    line_start: 45,
    line_end: 52,
    category: 'maintainability',
    severity: 'medium',
    rule: 'magic-numbers',
    title: 'Magic Numbers Without Context',
    description: 'These numeric literals lack context and make the code harder to understand. Define them as named constants with descriptive names explaining their purpose.',
    snippet: `export function calculateDiscount(price: number, tier: number) {
  if (tier === 1) {
    return price * 0.85;
  } else if (tier === 2) {
    return price * 0.72;
  } else if (tier === 3) {
    return price * 0.58;
  }
}`
  },
  {
    id: '9',
    file: 'src/api/routes.go',
    line_start: 123,
    line_end: 189,
    category: 'maintainability',
    severity: 'medium',
    rule: 'deep-nesting',
    title: 'Deeply Nested Logic',
    description: 'This code has 8 levels of nesting, making it very difficult to follow and maintain. Use early returns, guard clauses, or extract nested logic into separate functions.',
    snippet: `func ProcessRequest(req Request) Response {
    if req.Valid {
        if req.User != nil {
            if req.User.Active {
                if req.User.HasPermission("write") {
                    if req.Data != nil {
                        if len(req.Data) > 0 {
                            if validateData(req.Data) {
                                // Finally do something...`
  },
  {
    id: '10',
    file: 'src/lib/utils.rb',
    line_start: 301,
    line_end: 305,
    category: 'readability',
    severity: 'medium',
    rule: 'unclear-naming',
    title: 'Unclear Variable and Function Names',
    description: 'Variable names like "d", "tmp", and "x" provide no context about their purpose. Use descriptive names that explain what the data represents.',
    snippet: `def calc(d, x)
  tmp = d.map { |i| i * x }
  r = tmp.reduce(:+)
  return r / tmp.length
end`
  },
  {
    id: '11',
    file: 'src/components/Dashboard.tsx',
    line_start: 78,
    line_end: 83,
    category: 'readability',
    severity: 'low',
    rule: 'missing-documentation',
    title: 'Missing Function Documentation',
    description: 'This complex function lacks documentation explaining its parameters, return value, and side effects. Add JSDoc comments to improve code readability.',
    snippet: `function processUserAnalytics(user, timeRange, metrics, filters) {
  const data = fetchAnalytics(user.id, timeRange);
  const filtered = applyFilters(data, filters);
  const computed = calculateMetrics(filtered, metrics);
  return aggregateResults(computed);
}`
  },
  {
    id: '12',
    file: 'src/parser/tokenizer.php',
    line_start: 456,
    line_end: 456,
    category: 'readability',
    severity: 'low',
    rule: 'long-line',
    title: 'Excessively Long Line',
    description: 'This line contains 247 characters, making it difficult to read without horizontal scrolling. Break it into multiple lines or extract parts into variables.',
    snippet: `$result = $this->validator->validateAndTransform($input, ['strict' => true, 'allow_null' => false, 'max_length' => 500, 'min_length' => 10, 'pattern' => '/^[a-zA-Z0-9_-]+$/', 'custom_validator' => function($val) { return strlen($val) > 5; }]);`
  },
  {
    id: '13',
    file: 'src/middleware/auth.js',
    line_start: 34,
    line_end: 38,
    category: 'security',
    severity: 'medium',
    rule: 'weak-crypto',
    title: 'Weak Cryptographic Algorithm',
    description: 'Using MD5 for password hashing is cryptographically insecure. Use bcrypt, scrypt, or Argon2 for password hashing instead.',
    snippet: `function hashPassword(password) {
  const crypto = require('crypto');
  const hash = crypto.createHash('md5');
  return hash.update(password).digest('hex');
}`
  },
  {
    id: '14',
    file: 'src/handlers/file_upload.py',
    line_start: 67,
    line_end: 71,
    category: 'security',
    severity: 'high',
    rule: 'path-traversal',
    title: 'Path Traversal Vulnerability',
    description: 'Directly using user input to construct file paths can lead to path traversal attacks. Validate and sanitize the filename, or use a safe file storage system.',
    snippet: `def save_uploaded_file(filename, content):
    # DANGEROUS: User can provide "../../../etc/passwd"
    filepath = os.path.join('/uploads', filename)
    with open(filepath, 'wb') as f:
        f.write(content)`
  },
  {
    id: '15',
    file: 'src/services/cache.ts',
    line_start: 89,
    line_end: 112,
    category: 'code-smell',
    severity: 'low',
    rule: 'commented-code',
    title: 'Large Blocks of Commented Code',
    description: 'This file contains 23 lines of commented-out code. Dead code should be removed to improve readability. Use version control to preserve history.',
    snippet: `class CacheService {
  // async getFromCache(key: string) {
  //   const value = await redis.get(key);
  //   return JSON.parse(value);
  // }

  // async setInCache(key: string, value: any) {
  //   await redis.set(key, JSON.stringify(value));
  // }

  // ... 15 more lines of old commented code ...
  
  async get(key: string) {
    return this.store.get(key);
  }
}`
  },
  {
    id: '16',
    file: 'src/utils/string_helpers.java',
    line_start: 145,
    line_end: 167,
    category: 'maintainability',
    severity: 'low',
    rule: 'unused-variable',
    title: 'Unused Variables and Imports',
    description: 'This code declares variables and imports that are never used. Remove unused code to reduce clutter and potential confusion.',
    snippet: `import java.util.HashMap;
import java.util.ArrayList;
import java.io.File;  // Unused
import java.nio.Buffer;  // Unused

public String formatText(String input) {
    int unusedCounter = 0;  // Never referenced
    String tempValue = "default";  // Never read
    
    return input.trim().toLowerCase();
}`
  },
  {
    id: '17',
    file: 'src/models/user_service.py',
    line_start: 234,
    line_end: 267,
    category: 'code-smell',
    severity: 'medium',
    rule: 'feature-envy',
    title: 'Feature Envy Code Smell',
    description: 'This method accesses fields and methods of the User object more than its own class. Consider moving this logic into the User class itself.',
    snippet: `class UserService:
    def format_user_display(self, user):
        full_name = f"{user.first_name} {user.last_name}"
        email = user.email.lower()
        age = user.calculate_age()
        status = user.get_account_status()
        
        # 20+ more lines manipulating user object
        
        return formatted_data`
  },
  {
    id: '18',
    file: 'src/api/handlers.go',
    line_start: 445,
    line_end: 449,
    category: 'readability',
    severity: 'medium',
    rule: 'inconsistent-naming',
    title: 'Inconsistent Naming Convention',
    description: 'This code mixes camelCase, snake_case, and PascalCase naming conventions. Stick to Go\'s idiomatic naming conventions for consistency.',
    snippet: `func ProcessData(InputData string) {
    var user_name string
    var UserEmail string
    finalResult := calculate_value(InputData)
}`
  },
  {
    id: '19',
    file: 'src/controllers/order_controller.rb',
    line_start: 89,
    line_end: 127,
    category: 'maintainability',
    severity: 'high',
    rule: 'large-parameter-list',
    title: 'Too Many Function Parameters',
    description: 'This function takes 12 parameters, making it difficult to use and maintain. Consider grouping related parameters into objects or using the builder pattern.',
    snippet: `def create_order(user_id, product_id, quantity, price, discount, 
                 tax_rate, shipping_addr, billing_addr, payment_method, 
                 gift_wrap, delivery_date, special_instructions)
  # Function implementation...
end`
  },
  {
    id: '20',
    file: 'src/lib/validation.js',
    line_start: 201,
    line_end: 208,
    category: 'readability',
    severity: 'low',
    rule: 'complex-boolean',
    title: 'Complex Boolean Expression',
    description: 'This boolean expression is difficult to understand at a glance. Break it into smaller, named boolean variables or extract into a well-named function.',
    snippet: `if ((user.age >= 18 && user.verified && !user.suspended) || 
    (user.role === 'admin' || user.role === 'moderator') && 
    (user.permissions.includes('write') || user.permissions.includes('edit')) &&
    !user.flagged && user.email_confirmed) {
  // Proceed with action
}`
  }
];

export function generateMockResults(jobId: string): AnalysisResults {
  const byCategoryMap: Record<string, number> = {
    'security': 0,
    'code-smell': 0,
    'maintainability': 0,
    'readability': 0
  };

  const bySeverityMap: Record<string, number> = {
    'critical': 0,
    'high': 0,
    'medium': 0,
    'low': 0
  };

  mockFindings.forEach(finding => {
    byCategoryMap[finding.category]++;
    bySeverityMap[finding.severity]++;
  });

  const uniqueFiles = new Set(mockFindings.map(f => f.file));

  return {
    job_id: jobId,
    findings: mockFindings,
    summary: {
      total_issues: mockFindings.length,
      by_category: byCategoryMap as Record<'security' | 'code-smell' | 'maintainability' | 'readability', number>,
      by_severity: bySeverityMap as Record<'critical' | 'high' | 'medium' | 'low', number>,
      files_analyzed: uniqueFiles.size
    }
  };
}
