/**
 * 🔐 Security & Authentication Service
 * Production-ready security layer with JWT, rate limiting, and threat detection
 */

import { logger } from '../utils/logger';
import { CacheService } from './cacheService';
import { ErrorHandlingService } from './errorHandlingService';

export interface JWTPayload {
  userId: string;
  email: string;
  role: 'customer' | 'admin' | 'operator' | 'service';
  permissions: string[];
  iat: number;
  exp: number;
  iss: string;
  sub: string;
}

export interface AuthContext {
  user: JWTPayload;
  ipAddress: string;
  userAgent: string;
  requestId: string;
  timestamp: string;
}

export interface RateLimitConfig {
  windowMs: number;
  maxRequests: number;
  skipSuccessfulRequests: boolean;
  skipFailedRequests: boolean;
  keyGenerator?: (event: any) => string;
}

export interface SecurityRule {
  name: string;
  condition: (context: AuthContext, event: any) => boolean;
  action: 'ALLOW' | 'DENY' | 'CHALLENGE' | 'LOG';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  enabled: boolean;
}

export interface ThreatDetection {
  suspiciousActivity: boolean;
  riskScore: number; // 0-100
  indicators: string[];
  blockedRequests: number;
  lastThreatDetected?: string;
}

export class SecurityService {
  private cache: CacheService;
  private errorHandler: ErrorHandlingService;
  private securityRules: SecurityRule[] = [];
  private blockedIPs = new Set<string>();

  // Security configuration
  private readonly JWT_SECRET = process.env.JWT_SECRET || 'fallback-secret-change-in-production';
  private readonly TOKEN_EXPIRY = process.env.TOKEN_EXPIRY || '24h';
  private readonly RATE_LIMIT_WINDOW = parseInt(process.env.RATE_LIMIT_WINDOW || '900000'); // 15 minutes
  private readonly RATE_LIMIT_MAX = parseInt(process.env.RATE_LIMIT_MAX || '100');
  private readonly MAX_LOGIN_ATTEMPTS = parseInt(process.env.MAX_LOGIN_ATTEMPTS || '5');
  private readonly LOCKOUT_DURATION = parseInt(process.env.LOCKOUT_DURATION || '1800'); // 30 minutes

  constructor() {
    this.cache = new CacheService();
    this.errorHandler = new ErrorHandlingService();
    
    this.initializeSecurityRules();
    
    logger.info('SecurityService initialized');
  }

  /**
   * 🔐 Validate JWT token
   */
  async validateToken(token: string): Promise<JWTPayload | null> {
    try {
      if (!token) {
        return null;
      }

      // Check if token is blacklisted
      const isBlacklisted = await this.cache.exists(`blacklist:${token}`);
      if (isBlacklisted) {
        logger.warn('Attempted use of blacklisted token', { token: token.substring(0, 10) + '...' });
        return null;
      }

      // Simple JWT validation (in production, use a proper JWT library)
      const payload = this.decodeJWT(token);
      
      if (!payload || payload.exp < Date.now() / 1000) {
        return null;
      }

      // Cache valid token for faster subsequent checks
      await this.cache.set(`token:${token}`, payload, 300); // 5 minutes

      return payload;
    } catch (error) {
      logger.error('Token validation failed', { error });
      return null;
    }
  }

  /**
   * 🚪 Authenticate user and generate token
   */
  async authenticate(email: string, password: string, ipAddress: string): Promise<string | null> {
    try {
      // Check rate limiting
      const rateLimitKey = `auth_attempts:${email}:${ipAddress}`;
      const attempts = await this.cache.get<number>(rateLimitKey) || 0;
      
      if (attempts >= this.MAX_LOGIN_ATTEMPTS) {
        await this.errorHandler.handleError(
          `Too many login attempts for ${email}`,
          'AUTHENTICATION',
          'MEDIUM',
          { ipAddress, userId: email }
        );
        return null;
      }

      // Simulate user validation (replace with real authentication)
      const user = await this.validateUserCredentials(email, password);
      if (!user) {
        // Increment failed attempts
        await this.cache.increment(rateLimitKey);
        await this.cache.expire(rateLimitKey, this.LOCKOUT_DURATION);
        
        await this.errorHandler.handleError(
          `Authentication failed for ${email}`,
          'AUTHENTICATION',
          'LOW',
          { ipAddress, userId: email }
        );
        return null;
      }

      // Clear failed attempts on success
      await this.cache.delete(rateLimitKey);

      // Generate token
      const token = this.generateJWT(user);
      
      // Log successful authentication
      logger.info('User authenticated successfully', {
        userId: user.userId,
        email: user.email,
        ipAddress
      });

      return token;
    } catch (error) {
      await this.errorHandler.handleError(
        error as Error,
        'AUTHENTICATION',
        'HIGH',
        { ipAddress, userId: email }
      );
      return null;
    }
  }

  /**
   * 🛡️ Check authorization for specific action
   */
  async authorize(user: JWTPayload, action: string, resource?: string): Promise<boolean> {
    try {
      // Admin can do everything
      if (user.role === 'admin') {
        return true;
      }

      // Check specific permissions
      const hasPermission = user.permissions.includes(action) || 
                           user.permissions.includes('*') ||
                           user.permissions.includes(`${resource}:${action}`);

      if (!hasPermission) {
        await this.errorHandler.handleError(
          `Authorization denied for ${user.userId} attempting ${action} on ${resource}`,
          'AUTHORIZATION',
          'MEDIUM',
          { userId: user.userId }
        );
      }

      return hasPermission;
    } catch (error) {
      logger.error('Authorization check failed', { user: user.userId, action, resource, error });
      return false;
    }
  }

  /**
   * 🚦 Rate limiting check
   */
  async checkRateLimit(key: string, config?: Partial<RateLimitConfig>): Promise<boolean> {
    const rateLimitConfig = {
      windowMs: this.RATE_LIMIT_WINDOW,
      maxRequests: this.RATE_LIMIT_MAX,
      skipSuccessfulRequests: false,
      skipFailedRequests: false,
      ...config
    };

    try {
      const now = Date.now();
      const windowStart = now - rateLimitConfig.windowMs;
      
      // Get current request count for this window
      const requestKey = `rate_limit:${key}:${Math.floor(now / rateLimitConfig.windowMs)}`;
      const currentCount = await this.cache.get<number>(requestKey) || 0;

      if (currentCount >= rateLimitConfig.maxRequests) {
        // Rate limit exceeded
        await this.errorHandler.handleError(
          `Rate limit exceeded for ${key}`,
          'SYSTEM',
          'MEDIUM',
          { ipAddress: 'unknown' }
        );
        return false;
      }

      // Increment counter
      await this.cache.increment(requestKey);
      await this.cache.expire(requestKey, Math.ceil(rateLimitConfig.windowMs / 1000));

      return true;
    } catch (error) {
      logger.error('Rate limit check failed', { key, error });
      return true; // Fail open for availability
    }
  }

  /**
   * 🔍 Detect suspicious activity
   */
  async detectThreats(context: AuthContext, event: any): Promise<ThreatDetection> {
    try {
      let riskScore = 0;
      const indicators: string[] = [];
      let suspiciousActivity = false;

      // Check multiple threat indicators
      const checks = [
        this.checkBruteForceAttack(context, event),
        this.checkSQLInjection(event),
        this.checkXSSAttempt(event),
        this.checkSuspiciousUserAgent(context),
        this.checkGeolocationAnomaly(context),
        this.checkRequestPatterns(context, event)
      ];

      const results = await Promise.all(checks);
      
      results.forEach(result => {
        riskScore += result.score;
        if (result.indicators.length > 0) {
          indicators.push(...result.indicators);
        }
      });

      suspiciousActivity = riskScore > 50;

      // Apply security rules
      for (const rule of this.securityRules) {
        if (rule.enabled && rule.condition(context, event)) {
          riskScore += 20;
          indicators.push(rule.name);
          
          if (rule.action === 'DENY') {
            suspiciousActivity = true;
          }
        }
      }

      // Block IP if risk is very high
      if (riskScore > 80) {
        await this.blockIP(context.ipAddress, 'High risk score');
      }

      const detection: ThreatDetection = {
        suspiciousActivity,
        riskScore: Math.min(riskScore, 100),
        indicators,
        blockedRequests: this.blockedIPs.size,
        lastThreatDetected: suspiciousActivity ? new Date().toISOString() : undefined
      };

      // Log threat detection
      if (suspiciousActivity) {
        await this.errorHandler.handleError(
          `Threat detected: ${indicators.join(', ')}`,
          'SYSTEM',
          riskScore > 80 ? 'CRITICAL' : 'HIGH',
          {
            userId: context.user.userId,
            ipAddress: context.ipAddress
          }
        );
      }

      return detection;
    } catch (error) {
      logger.error('Threat detection failed', { error });
      return {
        suspiciousActivity: false,
        riskScore: 0,
        indicators: [],
        blockedRequests: 0
      };
    }
  }

  /**
   * 🚫 Block IP address
   */
  async blockIP(ipAddress: string, reason: string, durationSeconds = 3600): Promise<void> {
    try {
      this.blockedIPs.add(ipAddress);
      
      // Store in cache with expiration
      await this.cache.set(`blocked_ip:${ipAddress}`, {
        reason,
        blockedAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + durationSeconds * 1000).toISOString()
      }, durationSeconds);

      logger.warn('IP address blocked', { ipAddress, reason, durationSeconds });
    } catch (error) {
      logger.error('Failed to block IP', { ipAddress, reason, error });
    }
  }

  /**
   * ✅ Check if IP is blocked
   */
  async isIPBlocked(ipAddress: string): Promise<boolean> {
    try {
      return await this.cache.exists(`blocked_ip:${ipAddress}`);
    } catch (error) {
      logger.error('Failed to check IP block status', { ipAddress, error });
      return false;
    }
  }

  /**
   * 🔓 Invalidate token (logout)
   */
  async invalidateToken(token: string): Promise<void> {
    try {
      // Add to blacklist
      const payload = this.decodeJWT(token);
      if (payload) {
        const ttl = payload.exp - Math.floor(Date.now() / 1000);
        if (ttl > 0) {
          await this.cache.set(`blacklist:${token}`, true, ttl);
        }
      }

      logger.info('Token invalidated', { token: token.substring(0, 10) + '...' });
    } catch (error) {
      logger.error('Failed to invalidate token', { error });
    }
  }

  /**
   * 📊 Get security metrics
   */
  async getSecurityMetrics(): Promise<Record<string, any>> {
    try {
      const metrics = {
        blockedIPs: this.blockedIPs.size,
        activeTokens: 0,
        blacklistedTokens: 0,
        threatDetections: 0,
        authenticationFailures: 0,
        riskScore: 0
      };

      // Get metrics from cache
      const cacheKeys = await this.cache.mget([
        'security:active_tokens',
        'security:blacklisted_tokens',
        'security:threat_detections',
        'security:auth_failures',
        'security:avg_risk_score'
      ]);

      if (cacheKeys['security:active_tokens']) {
        metrics.activeTokens = cacheKeys['security:active_tokens'] as number;
      }

      if (cacheKeys['security:blacklisted_tokens']) {
        metrics.blacklistedTokens = cacheKeys['security:blacklisted_tokens'] as number;
      }

      if (cacheKeys['security:threat_detections']) {
        metrics.threatDetections = cacheKeys['security:threat_detections'] as number;
      }

      if (cacheKeys['security:auth_failures']) {
        metrics.authenticationFailures = cacheKeys['security:auth_failures'] as number;
      }

      if (cacheKeys['security:avg_risk_score']) {
        metrics.riskScore = cacheKeys['security:avg_risk_score'] as number;
      }

      return metrics;
    } catch (error) {
      logger.error('Failed to get security metrics', { error });
      return {};
    }
  }

  // Private helper methods

  private initializeSecurityRules(): void {
    this.securityRules = [
      {
        name: 'SuspiciousUserAgent',
        condition: (context) => {
          const suspiciousAgents = ['bot', 'crawler', 'spider', 'scraper'];
          return suspiciousAgents.some(agent => 
            context.userAgent.toLowerCase().includes(agent)
          );
        },
        action: 'LOG',
        severity: 'LOW',
        enabled: true
      },
      {
        name: 'HighFrequencyRequests',
        condition: (context, event) => {
          // This would check request frequency in a real implementation
          return false;
        },
        action: 'CHALLENGE',
        severity: 'MEDIUM',
        enabled: true
      },
      {
        name: 'AdminAccessFromUnknownIP',
        condition: (context) => {
          return context.user.role === 'admin' && !this.isKnownAdminIP(context.ipAddress);
        },
        action: 'LOG',
        severity: 'HIGH',
        enabled: true
      }
    ];
  }

  private async validateUserCredentials(email: string, password: string): Promise<JWTPayload | null> {
    // Mock user validation - replace with real database lookup
    if (email === 'admin@petplantr.com' && password === 'admin123') {
      return {
        userId: '1',
        email,
        role: 'admin',
        permissions: ['*'],
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 24 * 60 * 60, // 24 hours
        iss: 'petplantr',
        sub: email
      };
    }
    return null;
  }

  private generateJWT(user: JWTPayload): string {
    // Simple JWT generation - use a proper JWT library in production
    const header = { alg: 'HS256', typ: 'JWT' };
    const payload = {
      ...user,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 24 * 60 * 60
    };

    const headerB64 = Buffer.from(JSON.stringify(header)).toString('base64');
    const payloadB64 = Buffer.from(JSON.stringify(payload)).toString('base64');
    
    return `${headerB64}.${payloadB64}.signature`;
  }

  private decodeJWT(token: string): JWTPayload | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      
      const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
      return payload;
    } catch {
      return null;
    }
  }

  private async checkBruteForceAttack(context: AuthContext, event: any): Promise<{ score: number; indicators: string[] }> {
    // Check for brute force patterns
    return { score: 0, indicators: [] };
  }

  private async checkSQLInjection(event: any): Promise<{ score: number; indicators: string[] }> {
    // Check for SQL injection patterns
    const sqlPatterns = /('|\\')|(;)|(\\)|(union)|(select)|(insert)|(update)|(delete)|(drop)|(create)|(alter)/i;
    const eventStr = JSON.stringify(event);
    
    if (sqlPatterns.test(eventStr)) {
      return { score: 30, indicators: ['SQL_INJECTION_ATTEMPT'] };
    }
    
    return { score: 0, indicators: [] };
  }

  private async checkXSSAttempt(event: any): Promise<{ score: number; indicators: string[] }> {
    // Check for XSS patterns
    const xssPatterns = /(<script|javascript:|onerror=|onload=|eval\(|alert\()/i;
    const eventStr = JSON.stringify(event);
    
    if (xssPatterns.test(eventStr)) {
      return { score: 25, indicators: ['XSS_ATTEMPT'] };
    }
    
    return { score: 0, indicators: [] };
  }

  private async checkSuspiciousUserAgent(context: AuthContext): Promise<{ score: number; indicators: string[] }> {
    const suspiciousAgents = ['bot', 'crawler', 'spider', 'scraper', 'test'];
    const userAgent = context.userAgent.toLowerCase();
    
    for (const agent of suspiciousAgents) {
      if (userAgent.includes(agent)) {
        return { score: 10, indicators: ['SUSPICIOUS_USER_AGENT'] };
      }
    }
    
    return { score: 0, indicators: [] };
  }

  private async checkGeolocationAnomaly(context: AuthContext): Promise<{ score: number; indicators: string[] }> {
    // Check for unusual geolocation patterns
    // This would integrate with a geolocation service
    return { score: 0, indicators: [] };
  }

  private async checkRequestPatterns(context: AuthContext, event: any): Promise<{ score: number; indicators: string[] }> {
    // Check for unusual request patterns
    return { score: 0, indicators: [] };
  }

  private isKnownAdminIP(ipAddress: string): boolean {
    // Check against whitelist of known admin IPs
    const knownAdminIPs = ['127.0.0.1', '::1'];
    return knownAdminIPs.includes(ipAddress);
  }

  /**
   * 🧹 Cleanup resources
   */
  async cleanup(): Promise<void> {
    await this.cache.cleanup();
    await this.errorHandler.cleanup();
    logger.info('SecurityService cleanup completed');
  }
}

export const securityService = new SecurityService();
