import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import axios from 'axios'

type Side = 'buy' | 'sell'
type OrderType = 'market' | 'limit'

interface AccountSummary {
  total_value: number
  cash: number
  buying_power: number
  positions_value: number
  day_pnl: number
  day_pnl_pct: number
  total_pnl: number
  total_pnl_pct: number
}

interface Position {
  symbol: string
  quantity: number
  avg_cost: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
}

interface Order {
  id: string
  symbol: string
  side: Side
  order_type: string
  quantity: number
  price?: number | null
  status: string
  created_at: string
  updated_at: string
}

const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
})

const percentage = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 2,
})

export default function Trading() {
  const [account, setAccount] = useState<AccountSummary | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [statusMessage, setStatusMessage] = useState('Ready to place paper trades.')

  const [symbol, setSymbol] = useState('AAPL')
  const [quantity, setQuantity] = useState(10)
  const [side, setSide] = useState<Side>('buy')
  const [orderType, setOrderType] = useState<OrderType>('market')
  const [price, setPrice] = useState('')

  const fetchTradingData = useCallback(async (showSpinner: boolean) => {
    if (showSpinner) {
      setRefreshing(true)
    }
    try {
      const [accountRes, positionsRes, ordersRes] = await Promise.all([
        axios.get<AccountSummary>(`${API_BASE}/api/v1/trading/account`),
        axios.get<Position[]>(`${API_BASE}/api/v1/trading/positions`),
        axios.get<Order[]>(`${API_BASE}/api/v1/trading/orders`, {
          params: { limit: 50 },
        }),
      ])
      setAccount(accountRes.data)
      setPositions(positionsRes.data)
      setOrders(ordersRes.data)
      setErrorMessage('')
      setStatusMessage('Trading data synced.')
    } catch (error) {
      setErrorMessage('Unable to load trading data. Check that the backend is running.')
      setStatusMessage('Trading sync failed.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    void fetchTradingData(false)
  }, [fetchTradingData])

  const submitOrder = async (event: FormEvent) => {
    event.preventDefault()

    const cleanedSymbol = symbol.trim().toUpperCase()
    if (!cleanedSymbol) {
      setStatusMessage('Enter a symbol.')
      return
    }
    if (quantity <= 0) {
      setStatusMessage('Quantity must be greater than 0.')
      return
    }

    const payload: Record<string, unknown> = {
      symbol: cleanedSymbol,
      side,
      order_type: orderType,
      quantity,
    }

    if (orderType === 'limit') {
      const parsedPrice = Number.parseFloat(price)
      if (!Number.isFinite(parsedPrice) || parsedPrice <= 0) {
        setStatusMessage('Enter a valid limit price.')
        return
      }
      payload.price = parsedPrice
    }

    setSubmitting(true)
    setStatusMessage('Submitting order...')
    try {
      const res = await axios.post<Order>(`${API_BASE}/api/v1/trading/orders`, payload)
      setOrders((prev) => [res.data, ...prev.filter((item) => item.id !== res.data.id)])
      setStatusMessage(
        `${res.data.side.toUpperCase()} ${res.data.quantity} ${res.data.symbol} accepted (${res.data.status}).`,
      )
      setPrice('')
      await fetchTradingData(false)
    } catch (error) {
      const fallback = 'Order failed. Verify backend settings and try again.'
      if (axios.isAxiosError(error) && typeof error.response?.data?.detail === 'string') {
        setStatusMessage(error.response.data.detail)
      } else {
        setStatusMessage(fallback)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const topOrders = useMemo(() => orders.slice(0, 8), [orders])

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Trading</h1>
        <p className="page-subtitle mt-1">Live paper-trading desk with backend order routing</p>
      </div>

      {errorMessage ? (
        <div className="card border border-red-400/30 text-red-200">{errorMessage}</div>
      ) : null}

        <div className="section-grid section-grid--4 gap-4">
          <MetricCard
            title="Total Value"
            value={account ? currency.format(account.total_value) : loading ? 'Loading...' : '--'}
        />
        <MetricCard
          title="Cash"
          value={account ? currency.format(account.cash) : loading ? 'Loading...' : '--'}
        />
        <MetricCard
          title="Day P&L"
          value={
            account
              ? `${account.day_pnl >= 0 ? '+' : ''}${currency.format(account.day_pnl)} (${account.day_pnl_pct >= 0 ? '+' : ''}${percentage.format(account.day_pnl_pct)}%)`
              : loading
                ? 'Loading...'
                : '--'
          }
          valueClass={account && account.day_pnl >= 0 ? 'text-green-400' : 'text-red-400'}
        />
        <MetricCard
          title="Buying Power"
          value={account ? currency.format(account.buying_power) : loading ? 'Loading...' : '--'}
        />
      </div>

      <div className="section-grid section-grid--2 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="card-title">Positions</h2>
            <button
              type="button"
              onClick={() => void fetchTradingData(true)}
              className="btn-secondary"
              disabled={refreshing}
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
          <div className="overflow-x-auto">
              <table className="w-full">
              <thead>
                <tr className="text-left muted-text table-text">
                  <th className="pb-3">Symbol</th>
                  <th className="pb-3">Qty</th>
                  <th className="pb-3">Avg Cost</th>
                  <th className="pb-3">Current</th>
                  <th className="pb-3">Market Value</th>
                  <th className="pb-3">P&L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {positions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-6 muted-text table-text">
                      No open positions yet.
                    </td>
                  </tr>
                ) : (
                  positions.map((position) => (
                    <tr key={position.symbol} className="text-sm">
                    <td className="py-3 font-medium">{position.symbol}</td>
                      <td className="py-3">{position.quantity}</td>
                      <td className="py-3">{currency.format(position.avg_cost)}</td>
                      <td className="py-3">{currency.format(position.current_price)}</td>
                      <td className="py-3">{currency.format(position.market_value)}</td>
                      <td
                        className={`py-3 font-medium ${
                          position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}
                      >
                        {position.unrealized_pnl >= 0 ? '+' : ''}
                        {currency.format(position.unrealized_pnl)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2 className="card-title mb-4">Place Order</h2>
          <form className="space-y-4" onSubmit={submitOrder}>
            <div>
              <label className="field-label">Symbol</label>
              <input
                type="text"
                className="input w-full"
                value={symbol}
                onChange={(event) => setSymbol(event.target.value.toUpperCase())}
                placeholder="AAPL"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                className={`btn-primary ${side === 'buy' ? 'bg-green-600 hover:bg-green-500' : 'bg-white/10 hover:bg-white/20'}`}
                onClick={() => setSide('buy')}
              >
                Buy
              </button>
              <button
                type="button"
                className={`btn-primary ${side === 'sell' ? 'bg-red-600 hover:bg-red-500' : 'bg-white/10 hover:bg-white/20'}`}
                onClick={() => setSide('sell')}
              >
                Sell
              </button>
            </div>

            <div>
              <label className="field-label">Quantity</label>
              <input
                type="number"
                className="input w-full"
                value={quantity}
                min={1}
                onChange={(event) => setQuantity(Number.parseInt(event.target.value || '0', 10))}
              />
            </div>

            <div>
              <label className="field-label">Order Type</label>
              <select
                className="input w-full"
                value={orderType}
                onChange={(event) => setOrderType(event.target.value as OrderType)}
              >
                <option value="market">Market</option>
                <option value="limit">Limit</option>
              </select>
            </div>

              {orderType === 'limit' ? (
              <div>
                  <label className="field-label">Limit Price</label>
                <input
                  type="number"
                  className="input w-full"
                  value={price}
                  min={0}
                  step="0.01"
                  onChange={(event) => setPrice(event.target.value)}
                  placeholder="175.25"
                />
              </div>
            ) : null}

            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Submit Order'}
            </button>

            <p className="muted-text text-xs">{statusMessage}</p>
          </form>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title mb-4">Execution Feed</h2>
        <div className="space-y-3">
          {topOrders.length === 0 ? (
            <p className="table-text muted-text">No orders yet.</p>
          ) : (
            topOrders.map((order) => (
              <div key={order.id} className="flex items-center justify-between surface-row p-3">
                <div>
                  <p className="text-sm font-semibold">
                    {order.side.toUpperCase()} {order.quantity} {order.symbol}
                  </p>
                  <p className="muted-text text-xs">
                    {order.order_type.toUpperCase()}
                    {order.price ? ` @ ${currency.format(order.price)}` : ''}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-semibold uppercase text-primary-300">{order.status}</p>
                  <p className="muted-text text-xs">{new Date(order.updated_at).toLocaleTimeString()}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function MetricCard({
  title,
  value,
  valueClass,
}: {
  title: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="card">
      <p className="field-label">{title}</p>
      <p className={`metric-value mt-2 ${valueClass ?? ''}`}>{value}</p>
    </div>
  )
}
