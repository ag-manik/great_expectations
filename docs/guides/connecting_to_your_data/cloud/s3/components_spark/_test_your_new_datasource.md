import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';
import TechnicalTag from '@site/docs/term_tags/_tag.mdx';

Verify your new <TechnicalTag tag="datasource" text="Datasource" /> by loading data from it into a <TechnicalTag tag="validator" text="Validator" /> using a <TechnicalTag tag="batch_request" text="Batch Request" />.

<Tabs
  defaultValue='runtime_batch_request'
  values={[
  {label: 'Specify an S3 path to single CSV', value:'runtime_batch_request'},
  {label: 'Specify a data_asset_name', value:'batch_request'},
  ]}>

<TabItem value="runtime_batch_request">

Add the S3 path to your CSV in the `path` key under `runtime_parameters` in your `RuntimeBatchRequest`.

:::tip
The path you will want to use is your S3 URI, not the URL.
:::

```python file=../../../../../../tests/integration/docusaurus/connecting_to_your_data/cloud/s3/spark/inferred_and_runtime_yaml_example.py#L57-L63
```

Then load data into the `Validator`.

```python file=../../../../../../tests/integration/docusaurus/connecting_to_your_data/cloud/s3/spark/inferred_and_runtime_yaml_example.py#L71-L77
```

</TabItem>

<TabItem value="batch_request">

Add the name of the <TechnicalTag tag="data_asset" text="Data Asset" /> to the `data_asset_name` in your `BatchRequest`.

```python file=../../../../../../tests/integration/docusaurus/connecting_to_your_data/cloud/s3/spark/inferred_and_runtime_yaml_example.py#L83-L88
```

Then load data into the `Validator`.

```python file=../../../../../../tests/integration/docusaurus/connecting_to_your_data/cloud/s3/spark/inferred_and_runtime_yaml_example.py#L96-L102
```

</TabItem>

</Tabs>