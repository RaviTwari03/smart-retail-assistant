import Layout from "../components/Layout";

function InventoryPage() {

  const inventory = [

    {
      product: "Laptop",
      stock: 12,
      status: "Low"
    },

    {
      product: "Headphones",
      stock: 42,
      status: "Healthy"
    },

    {
      product: "Keyboard",
      stock: 5,
      status: "Critical"
    }

  ];

  return (

    <Layout>

      <h1>Inventory Analytics</h1>

      <table style={{
        width: "100%",
        marginTop: "30px",
        borderCollapse: "collapse"
      }}>

        <thead>

          <tr>

            <th style={tableHeader}>
              Product
            </th>

            <th style={tableHeader}>
              Stock
            </th>

            <th style={tableHeader}>
              Status
            </th>

          </tr>

        </thead>

        <tbody>

          {
            inventory.map((item, index) => (

              <tr key={index}>

                <td style={tableCell}>
                  {item.product}
                </td>

                <td style={tableCell}>
                  {item.stock}
                </td>

                <td style={tableCell}>
                  {item.status}
                </td>

              </tr>
            ))
          }

        </tbody>

      </table>

    </Layout>
  );
}

const tableHeader = {
  border: "1px solid #334155",
  padding: "12px",
  backgroundColor: "#1e293b"
};

const tableCell = {
  border: "1px solid #334155",
  padding: "12px"
};

export default InventoryPage;