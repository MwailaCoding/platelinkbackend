import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const url = request.nextUrl.clone();
  
  // If user is accessing root, redirect to dashboard or login
  if (url.pathname === '/') {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  
  // Example for handling branch context via cookies in the future
  // const branchId = request.cookies.get('selected_branch_id')?.value;
  // if (url.pathname.startsWith('/dashboard') && !branchId) {
  //   // Could redirect to branch selection if strict enforcement is needed
  //   // return NextResponse.redirect(new URL('/branches', request.url));
  // }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/', '/dashboard/:path*'],
};
