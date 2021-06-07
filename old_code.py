# plotting sentinel images and mação
for polygon1 in list(products_df.footprint):
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    gpd.GeoSeries(polygon1).plot(ax=ax, color='red')
    gpd.GeoSeries(macao_outer_square).plot(ax=ax, color='grey')
    gpd.GeoSeries(macao_shp).plot(ax=ax, color='blue')
    print(macao_shp.intersection(polygon1).area/macao_shp.area)
    plt.show()
    
# "old" way to get products
api = SentinelAPI('fernandeslouro', 'copernicospw', 'https://scihub.copernicus.eu/dhus')
products = api.query(macao_outer_square,
                     date=(date.today() - timedelta(7), date.today()),
                     platformname='Sentinel-2',
                     cloudcoverpercentage=(0, 30))
products_df = api.to_dataframe(products)
products_df['footprint'] = geopandas.GeoSeries.from_wkt(products_df['footprint'])
products_df = gpd.GeoDataFrame(products_df, geometry='footprint')
products_df['intersection_area'] = products_df.apply(lambda row: macao_shp.intersection(row.footprint).area/macao_shp.area, axis=1)