/**
 * Core Database Data Access Layer (DAL)
 * =====================================
 * Includes:
 * 1. Prisma Client Singleton (HMR safe)
 * 2. Standardized Error Interceptor
 * 3. Repository Wrapper (UserRepository)
 * 4. Transactional Seed Script
 */

import { PrismaClient, Prisma, User } from '@prisma/client';

// ============================================================================
// 1. PRISMA SINGLETON (CONNECTION MANAGER)
// ============================================================================

/**
 * Global caching prevents Node.js from exhausting database connections
 * every time a file changes and triggers Hot Module Replacement (HMR) in dev.
 */
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

// ============================================================================
// 2. CENTRALIZED ERROR HANDLING
// ============================================================================

export class AppError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
    this.name = 'AppError';
  }
}

/**
 * Translates generic Prisma errors into safe, HTTP-friendly application errors.
 * Prevents database internal details from leaking to the frontend.
 */
export function handlePrismaError(error: unknown): never {
  if (error instanceof Error && 'code' in error) {
    const code = (error as any).code;
    switch (code) {
      case 'P2002':
        // Unique constraint failed
        const target = (error as any).meta?.target as string[] | undefined;
        throw new AppError(409, `Conflict: A record with this ${target?.join(', ') || 'field'} already exists.`);
      case 'P2025':
        // Record not found
        throw new AppError(404, 'Not Found: The requested record does not exist.');
      case 'P2003':
        // Foreign key constraint failed
        throw new AppError(400, 'Bad Request: Invalid reference to a related record.');
      default:
        console.error(`[Prisma Error ${code}]:`, error.message);
        throw new AppError(500, 'An unexpected database error occurred.');
    }
  }

  // Fallback for unknown errors (e.g. connection drops)
  console.error('[Database Error]:', error);
  throw new AppError(500, 'Internal Server Error');
}

// ============================================================================
// 3. THE REPOSITORY PATTERN
// ============================================================================

/**
 * Type aliases utilizing Prisma's auto-generated utility types
 * to ensure full type-safety for payload arguments.
 */
export type CreateUserInput = Prisma.UserCreateInput;
export type UpdateUserInput = Prisma.UserUpdateInput;

export type UserWithProfile = Prisma.UserGetPayload<{
  include: { profile: true };
}>;

export type UserWithRelations = Prisma.UserGetPayload<{
  include: { profile: true; posts: true };
}>;

export class UserRepository {
  
  /**
   * Create a user and their profile simultaneously using nested writes.
   */
  static async createUser(data: CreateUserInput): Promise<UserWithProfile> {
    try {
      return await prisma.user.create({
        data,
        include: { profile: true },
      });
    } catch (error) {
      handlePrismaError(error);
    }
  }

  /**
   * Retrieve a user safely. Throws a clean 404 AppError if missing.
   */
  static async getUserById(id: string): Promise<UserWithRelations> {
    try {
      return await prisma.user.findUniqueOrThrow({
        where: { id },
        include: { profile: true, posts: true },
      });
    } catch (error) {
      handlePrismaError(error);
    }
  }

  /**
   * Finds all active users with pagination.
   */
  static async listUsers(skip: number = 0, take: number = 10): Promise<any[]> {
    try {
      return await prisma.user.findMany({
        skip,
        take,
        orderBy: { createdAt: 'desc' },
      });
    } catch (error) {
      handlePrismaError(error);
    }
  }
}

// ============================================================================
// 4. DATABASE SEEDING
// ============================================================================

/**
 * Designed to be executed via `npx prisma db seed`.
 * Uses $transaction to ensure the seed either fully succeeds or fully rolls back.
 */
export async function seedDatabase() {
  console.log('🌱 Starting database seed...');

  try {
    await prisma.$transaction(async (tx) => {
      const admin = await tx.user.upsert({
        where: { email: 'admin@bugfixer.local' },
        update: {},
        create: {
          email: 'admin@bugfixer.local',
          password: 'hashed_password_mock', // Usually hashed via bcrypt
          role: 'SUPER_ADMIN',
          profile: { create: { bio: 'System Administrator' } },
        },
      });
      console.log(`✅ Admin user seeded: ${admin.id}`);
    });
  } catch (error) {
    console.error('❌ Failed to seed database:', error);
  }
}