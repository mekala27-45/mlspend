import Ledger from '../ledger';
import { routes } from '../routes';
export function generateStaticParams() { return routes.filter(([id])=>id!=='statement').map(([route])=>({route})); }
export const dynamicParams = false;
export default async function Page({params}: {params: Promise<{route: string}>}) {
  const {route} = await params;
  return <Ledger route={route}/>;
}
